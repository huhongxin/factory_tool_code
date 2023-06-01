'''
在 Linux 环境下，您可以使用以下命令将 python 程序运行在后台：

```
nohup python render.py > output.log &
```
nohup: 表示运行程序时忽略挂起信号，即程序不受终端关闭等事件的影响，始终在后台持续运行。
python: 表示要运行的 Python 程序文件，即 render.py。
>: 表示将程序的标准输出重定向到指定文件，这里是 output.log。
&: 表示将程序放入后台运行，不占用终端。

如何关闭这个程序：
1. 使用ps ax | grep render.py 查看程序的PID
2. kill <PID>
'''

# server 类型
NONE = -1
SOPS = 0
HUB_PORTAL = 1
CLOUD = 2

# 设置这里选择服务器类型
SERVER_TYPE = NONE

if SERVER_TYPE == SOPS:
    # sops 服务器配置示例
    URL = "http://192.168.66.59/api/v2/key/"
    API_KEY = "39468653-092d-4b7f-ac0a-ef21668ee11a"

elif SERVER_TYPE == HUB_PORTAL:
    # hub portal API，配置示例
    URL = "http://192.168.66.80/key/"
    API_KEY = "e8db079d-9113-7abc-83eb-5baf819e583f"
    HUB = "MC90380C612CC0"

elif SERVER_TYPE == CLOUD:
    # 云服务器API，配置示例
    URL = "https://api.sync-sign.com/v2/key/"
    API_KEY = "1ac4042e-0e0c-4480-ab1d-b6aa61a5db60"

else:
    print("!!! 请给config文件中的SERVER_TYPE设置类型 !!!!!")

# 不通过接口获取某个hub的node列表，直接指定要刷新nodeID
TARGET_LIST = []

# 如果通过接口，获取了很多的nodeId, 那么可以通过这里只选择D29C-LE,D42C-LE,D75-LEWI中的一种或者全部的ble display
SERVER_TYPEL_NONE = None
SERVER_TYPEL_D29 = 'D29C-LE'
SERVER_TYPEL_D42 = 'D42C-LE'
SERVER_TYPEL_D75 = 'D75C-LEWI'
SERVER_TYPEL_LIST = [SERVER_TYPEL_D29, SERVER_TYPEL_D42, SERVER_TYPEL_D75]
TARGET_DISPLAY_MODEL = SERVER_TYPEL_D75

# 不想刷新的node，如果通过接口获取了某个hub下的所有node，但有一些node并不需要被更新，那么就将nodeid填到这里
NG_LIST = []

# 每次请求isRender结果的间隔(s)
WAIT_RENDER_TIME_ONE = 20

# 请求isRender结果的最大次数
WAIT_RENDER_RESULT_CNT = 9

# 两次推送layout的时间间隔(s),就是获取了上一次的isRender结果以后，到下一次post render的间隔
RENDER_INTERVAL_TWICE = 60

# 钉钉机器人的配置
ENABLE_DINGDING_NOTIFY = True # 开启通知
NOTIFY_ONLY_FAIL = True # 只有失败的时候才通知
# 通知的链接
WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=f18c08a42fb065a8151a6630dfad98bd3e15a4c8dd3441f15fa526fb8d7e4339"

# 刷屏次数的记录，文件名
FILE_RECORD = 'record'

# 显示时间用到的时区
TIME_ZONE = 8 # 时区是8

# 监控刷屏任务有没有死，如果n分钟都没有更新时间戳，就任务任务死了，需要重新运行render任务(min)
MONITOR_TIME = 10

# 监控器检查任务的时间间隔(min)
MONITOR_SLEEP_TIME = 3