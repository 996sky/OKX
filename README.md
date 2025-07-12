# OKX 自动赎回、自动从资金账户转入交易账户脚本
这是为了每天定投 BTC 而编写的脚本。  
OKX官方有定投 BTC 的机器人，但需要手动操作赎回存在自动赚币账户中的 USDT。这个脚本可以自动赎回 USDT，并将资金账户的 USDT 转入交易账户。
## 使用方式
### 配合青龙面板使用
#### 安装青龙面板
```bash
docker run -dit \                           # -d 后台运行，-i 保留标准输入，-t 分配伪终端
  -v /qinglong/data:/ql/data \              # 将宿主机 /qinglong/data 挂载到容器 /ql/data，持久化配置
  -p 5700:5700 \                            # 宿主机 5700 端口映射到容器 5700 端口
  -e QlBaseUrl="/" \                        # 设置面板访问路径前缀为根目录 /
  -e QlPort="5700" \                        # 设置容器内程序监听端口为 5700
  --name qinglong \                         # 为容器指定名称 qinglong，方便后续管理
  --hostname qinglong \                     # 设置容器内部主机名为 qinglong
  --restart unless-stopped \                # Docker 或宿主机重启后自动启动，除非手动停止
  whyour/qinglong:latest                    # 使用 whyour/qinglong 镜像的 latest 标签
```
#### 配置脚本
1. 将 `redeem_usdt.py` 放入青龙面板的 `/ql/data/scripts` 目录下。
2. 在青龙面板中添加环境变量：
   - `USE_TG`: (可选)是否使用 Telegram 通知（`True` 或 `False`）默认值为 `False`
   - `TG_BOT_TOKEN`: (可选)Telegram Bot Token
   - `TG_USER_ID`: (可选)Telegram 用户 ID
   - `TG_API_HOST`: (可选)Telegram API Host
   - `API_KEY`: OKX API Key
   - `SECRET_KEY`: OKX Secret Key
   - `PASSPHRASE`: OKX Passphrase
   - `AMOUNT`: (可选)你要赎回的金额，默认值为 `3`
3. 在青龙面板中添加定时任务，设置脚本执行频率（例如每天执行一次）

### 手动运行
crontab 中添加以下行：
```bash
# 每天午夜 0 点执行脚本 redeem_usdt.py，并将输出追加到 usdt.log 中
0 0 * * * /usr/bin/python3 /path/to/redeem_usdt.py >> /path/to/usdt.log 2>&1
# cron表达式说明
# * * * * * command_to_run
# | | | | |
# | | | | └───── 星期几 (0 - 7) (星期日是 0 或 7)
# | | | └──────── 月份 (1 - 12)
# | | └──────────── 日 (1 - 31)
# | └──────────────── 小时 (0 - 23)
# └──────────────────── 分钟 (0 - 59)

# examples:
# 表达式         含义
# -------------------------------------
# * * * * *     每分钟执行一次
# 0 * * * *     每小时的第 0 分钟（整点）执行一次
# 0 0 * * *     每天午夜（0点）执行一次
# 0 9 * * 1-5   每周一到周五的早上 9 点执行
# */5 * * * *   每 5 分钟执行一次
# 0 12 1 * *    每月 1 日中午 12 点执行
# 0 0 1 1 *     每年 1 月 1 日 0 点执行
```