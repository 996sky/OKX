#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Simple Earn (简单赚币）赎回 USDT 并将其转移到现货/交易账户
使用官方 python-okx SDK 而不是手动签名 REST 调用。

执行步骤:
    1. 从储蓄(Simple Earn Flexible)赎回指定数量的 USDT。
    2. 将赎回的资金从资金账户 (18) 转移到现货/交易账户 (6)。

所需环境变量 ▶️（在 shell 或 .env 文件中设置）:
    API_KEY        OKX API 密钥
    SECRET_KEY     OKX 密钥
    PASSPHRASE     OKX 密码短语
    AMOUNT         要赎回并转移的 USDT 数量。默认为 "3"。

可选的 Telegram 推送 ▶️
    USE_TG         设置为 "1" 启用 Telegram 通知（其他值禁用）
    TG_BOT_TOKEN   Bot 令牌
    TG_USER_ID     聊天 ID
    TG_API_HOST    (可选)Telegram API 主机，默认为 "api.telegram.org"

安装 SDK:
    pip install python-okx

测试环境: python-okx==0.3.9 (2025-05-12)
"""

import os
import time
import requests
from okx import Funding, Asset

# ─── 环境配置 ────────────────────────────────────────────────────────────────
USE_TG       = os.getenv("USE_TG").lower() in ("1", "true", "yes")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_USER_ID   = os.getenv("TG_USER_ID")
TG_API_HOST  = os.getenv("TG_API_HOST", "api.telegram.org")

API_KEY      = os.getenv("API_KEY")
SECRET_KEY   = os.getenv("SECRET_KEY")
PASSPHRASE   = os.getenv("PASSPHRASE")

# 基本校验 — 保持最小化；若凭证缺失则及早抛错
required = [API_KEY, SECRET_KEY, PASSPHRASE]
if USE_TG:
    required.extend([TG_BOT_TOKEN, TG_USER_ID])
if not all(required):
    raise EnvironmentError("缺少必要的环境变量。")

# ─── 辅助函数 ────────────────────────────────────────────────────────────────

def telegram(msg: str) -> None:
    """如果启用 TG 集成，则发送 Telegram 消息。"""
    if not USE_TG:
        return
    payload = {"chat_id": TG_USER_ID, "text": msg}
    url = f"https://{TG_API_HOST}/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, timeout=10, data=payload)
        r.raise_for_status()
        print("✅ 已发送 Telegram 推送")
    except requests.RequestException as exc:
        print(f"❌ Telegram 推送失败: {exc}")

# ─── SDK 客户端 ────────────────────────────────────────────────────────────────
# use_server_time=False 保持本地时间戳，除非时钟漂移有问题
funding = Funding(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=0)
asset   = Asset  (API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=0)

# ─── 核心业务逻辑 ─────────────────────────────────────────────────────────────

def redeem_savings(ccy: str, amt: str):
    """从 Simple Earn Flexible (储蓄) 赎回 amt 数量的 ccy。"""
    body = {"ccy": ccy, "side": "redempt", "amt": amt}
    return funding.savings_purchase_redempt(**body)


def transfer_funds(ccy: str, amt: str):
    """将 amt 数量的 ccy 从资金账户 (18) 转到现货/交易账户 (6)。"""
    body = {"ccy": ccy, "amt": amt, "from": "18", "to": "6"}
    return asset.transfer(**body)

# ─── 执行流程 ────────────────────────────────────────────────────────────────

def main():
    ccy  = "USDT"
    amt  = os.getenv("AMOUNT", "3")

    # 1️⃣ 赎回
    redeem_resp = redeem_savings(ccy, amt)
    print("赎回响应:", redeem_resp)
    telegram(f"已赎回 {amt} {ccy} 从 Simple Earn:\n{redeem_resp}")

    # 给 OKX 一点时间完成赎回，以便余额可用
    time.sleep(1)

    # 2️⃣ 转账
    transfer_resp = transfer_funds(ccy, amt)
    print("转账响应:", transfer_resp)
    telegram(f"已将 {amt} {ccy} 转入现货账户:\n{transfer_resp}")


if __name__ == "__main__":
    main()
