'''
在 Linux 环境下，您可以使用以下命令将 python 程序运行在后台：

```
nohup python render.py > output.log &
```

在这里，`nohup` 命令允许在不登出系统的情况下运行程序，并且在终端关闭后程序仍然在运行。

`> output.log` 表示将标准输出重定向到一个文件 `output.log` 中，因此您可以使用该文件查看程序的日志输出。

最后，`&` 表示将程序放在后台运行。

请注意，在运行时，您可以使用 `ps` 命令查看程序的进程状态，并使用 `kill` 命令终止程序的运行
'''


# API 类型
SOPS = 0
HUB_PORTAL = 1
CLOUD = 2

# sops 服务器配置示例
URL = "http://192.168.66.59/api/v2/key/"
API_KEY = "7adc7da1-16e8-461e-bc93-9b59093a6a94"
HUB = "MC1097BD4052C4"
MODE = SOPS

# hub portal API，配置示例
# URL = "http://192.168.66.80/key/"
# API_KEY = "e8db079d-9113-7abc-83eb-5baf819e583f"
# HUB = "MC90380C612CC0"
# MODE = HUB_PORTAL

# 云服务器API，配置示例
# URL = "https://api.sync-sign.com/v2/key/"
# API_KEY = "71e6c4e6-530c-4d7d-b2ea-551d6d1671e6"
# HUB = 'MC1C9DC2585C04'
# MODE = CLOUD


# 不想刷新的node，如果通过接口获取了某个hub下的所有node，但有一些node并不需要被更新，那么就将nodeid填到这里
NG_LIST = []

# 不合并从hub 的node接口获取到的nodeId
NOT_MERGES = True

# 不通过接口获取某个hub的node列表，直接指定要刷新nodeID
TARGET_LIST = []

# 显示时间用到的时区
TIME_ZONE = 8 # 时区是8

# 只刷新BLE dispalay
ONLYBLE = True

# 每次请求isRender结果的间隔(s)
WAIT_RENDER_TIME_ONE = 20

# 请求isRender结果的最大次数
WAIT_RENDER_RESULT_CNT = 9

# 两次推送layout的时间间隔(s)
RENDER_INTERVAL_TWICE = 60

# 刷屏次数的记录，文件名
FILE_RECORD = 'record'

# 钉钉机器人的配置
# 开启通知
ENABLE_DINGDING_NOTIFY = True

# 只有失败的时候才通知
NOTIFY_ONLY_FAIL = True

# 通知的链接
WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=f18c08a42fb065a8151a6630dfad98bd3e15a4c8dd3441f15fa526fb8d7e4339"

# 监控刷屏任务有没有死，如果n分钟都没有更新时间戳，就任务任务死了，需要重新运行render任务(min)
MONITOR_TIME = 10

# 监控器检查任务的时间间隔(min)
MONITOR_SLEEP_TIME = 3