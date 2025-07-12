#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import hmac
import base64
import hashlib
import requests
import datetime
import os # 读取环境变量

# 需要设置以下环境变量。也可以写在默认值中，如 TG_USER_ID = os.getenv("TG_USER_ID", "123456789")，或直接赋值。但为了安全起见，建议在环境变量中设置。

USE_TG = os.getenv("USE_TG", "").lower() in ("1", "true", "yes")  # 若需 Telegram 推送则设为 True
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN") # Telegram Bot Token
TG_USER_ID = os.getenv("TG_USER_ID") # Telegram 用户 ID
TG_API_HOST = os.getenv("TG_API_HOST", "api.telegram.org") # 如果使用代理或自定义域名，可以设置此变量

API_KEY = os.getenv("API_KEY") # OKX API Key
SECRET_KEY = os.getenv("SECRET_KEY") # OKX Secret Key
PASSPHRASE = os.getenv("PASSPHRASE") # OKX Passphrase
if not (USE_TG and TG_BOT_TOKEN and TG_USER_ID and API_KEY and SECRET_KEY and PASSPHRASE):
    raise ValueError("请设置所有必需的环境变量。")

BASE_URL = "https://www.okx.com" 

# ——— 工具函数 ———
def telegram(msg: str):
    """发送 Telegram 消息。"""
    if not USE_TG:
        return
    payload = {'chat_id': TG_USER_ID, 'text': msg}
    url = f'https://{TG_API_HOST}/bot{TG_BOT_TOKEN}/sendMessage'
    r = requests.post(url, data=payload)
    print('TG 推送成功' if r.status_code == 200 else 'TG 推送失败')

def get_timestamp() -> str:
    """返回 ISO 8601 格式的当前 UTC 时间戳。"""
    return datetime.datetime.now(datetime.timezone.utc) \
        .isoformat("T", "milliseconds") \
        .replace("+00:00", "Z")

def sign(method: str, path: str, body: str, timestamp: str) -> str:
    """返回 OKX HMAC-SHA256 签名。"""
    msg = f"{timestamp}{method}{path}{body}"
    h = hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256)
    return base64.b64encode(h.digest()).decode()

def api_post(path: str, params: dict) -> dict:
    """通用的 OKX REST API POST 请求。"""
    ts = get_timestamp()
    body = json.dumps(params)
    sig = sign("POST", path, body, ts)
    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }
    url = BASE_URL + path
    r = requests.post(url, headers=headers, data=body)
    return r.json()

def api_get(path: str, params: dict = None) -> dict:
    """通用的 OKX REST API GET 请求。"""
    if params:
        path += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    ts = get_timestamp()
    body = ""
    sig = sign("GET", path, body, ts)
    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }
    url = BASE_URL + path
    r = requests.get(url, headers=headers)
    return r.json()     

# ——— 业务逻辑 ———
def transfer_to_trading(ccy: str, amt: str) -> dict:
    """
    从资金账户转账到现货账户。
    OKX 接口: POST /api/v5/asset/transfer
    from: "18" (资金账户), to: "6" (现货账户)
    """
    path = "/api/v5/asset/transfer"
    params = {
        "ccy": ccy,
        "amt": amt,
        "from": "6",
        "to": "18"
    }
    return api_post(path, params)

def transfer_to_funding(ccy: str, amt: str) -> dict:
    """
    从现货账户转账到资金账户。
    OKX 接口: POST /api/v5/asset/transfer
    from: "6" (现货账户), to: "18" (资金账户)
    """
    path = "/api/v5/asset/transfer"
    params = {
        "ccy": ccy,
        "amt": amt,
        "from": "18",
        "to": "6"
    }
    return api_post(path, params)

def redeem_savings(ccy: str, amt: str) -> dict:
    """
    赎回活动中的存币。
    OKX 接口: POST /api/v5/finance/savings/purchase-redempt
    side: "redempt" 表示赎回
    """
    path = "/api/v5/finance/savings/purchase-redempt"
    params = {"ccy": ccy, "amt": amt, "side": "redempt"}
    return api_post(path, params)

def get_trading_balance(ccy: str = "USDT") -> str:
    """
    获取交易账户的可用余额 (cashBal)
    OKX 接口: GET /api/v5/account/balance
    """
    path   = "/api/v5/account/balance"
    params = {"ccy": ccy}

    resp  = api_get(path, params)      # consider switching to GET – see below
    print(resp)  # 调试输出
    data  = resp.get("data", [])

    if not data:                        # nothing came back
        return "0"

    for d in data[0].get("details", []):
        if d.get("ccy") == ccy:
            return d.get("cashBal", "0")

    return "0"                          # currency not present

def main():
    ccy, amt = "USDT", os.getenv("AMOUNT", "3")  # 去环境变量获取金额，默认为 3 USDT 

    # 1) 赎回
    r_result = redeem_savings(ccy, amt)
    print("赎回结果:", r_result)
    telegram(f"赎回 {amt} {ccy}: \n{r_result}")

    # 延迟1秒，确保赎回完成
    time.sleep(1)

    # 2) 转账: 资金账户 → 交易账户
    t_result = transfer_to_trading(ccy, amt)
    print("转账结果:", t_result)
    telegram(f"将 {amt} {ccy} 从资金账户转至交易账户: \n{t_result}")

    # 3) 获取BTC交易账户余额, 并转账至资金账户
    btc_balance = get_trading_balance("BTC")
    print(f"BTC 交易账户余额: {btc_balance}")
    telegram(f"BTC 交易账户余额: \n{btc_balance}")
    if float(btc_balance) > 0:
        transfer_result = transfer_to_funding("BTC", btc_balance)
        print("转账结果:", transfer_result)
        telegram(f"将 {btc_balance} BTC 从交易账户转至资金账户: \n{transfer_result}")
    else:
        print("BTC 交易账户余额为 0, 无需转账。")
        telegram("BTC 交易账户余额为 0, 无需转账。")

if __name__ == "__main__":
    main()