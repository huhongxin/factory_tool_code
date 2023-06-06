import httpx
import json
import datetime
import asyncio
import logging as log
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from layout import SHOW_NODEID
import config
import time

log.basicConfig(level=log.INFO)

class SingletonWEBAPI:
    __instance = None

    def __init__(self):
        if SingletonWEBAPI.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            SingletonWEBAPI.__instance = self
            self.status = {}
            self.nodeInfo = {}
            self.taskMap  = {}
            self.nodeNumber = 0
            self.modifyCount = 0
            self.layout = self.getLayout(SHOW_NODEID)

    @staticmethod 
    def getInstance():
        if SingletonWEBAPI.__instance == None:
            SingletonWEBAPI()
        return SingletonWEBAPI.__instance

    def pathGetSn(self):
        return config.URL+config.API_KEY+"/devices"

    def pathGetRenderSta(self,renderId):
        return config.URL+config.API_KEY+"/renders/"+renderId

    def setStatus(self,nodeId,isRendered):
        if nodeId not in self.status:
            self.status[nodeId] = {'success':0,'fail':0}
        if isRendered:
            self.status[nodeId]['success'] += 1
        else:
            self.status[nodeId]['fail'] += 1
        # 为了不让文件频繁保存
        self.modifyCount += 1
        if self.modifyCount >= self.nodeNumber * 2:
            self.modifyCount = 0
            self.writeFile()

    def writeFile(self):
        with open(config.FILE_RECORD, 'w+') as file:
            json.dump(self.status, file)
        log.info("save file ok")

    def readFile(self):
        try:
            with open(config.FILE_RECORD, 'r') as file:
                self.status = json.load(file)
                log.info("read data from file: %s",self.status)
        except IOError:
            log.info("not exit file %s", config.FILE_RECORD)

    def pathGetNodeId(self,HUB_SN):
        return config.URL + config.API_KEY +"/devices/" + HUB_SN + "/nodes"

    def pathGetBleNodeId(self):
        return config.URL + config.API_KEY + "/nodes"

    def pathSetTriggers(self, nodeId):
        return config.URL + config.API_KEY + "/nodes/" + nodeId + "/triggers"

    def pathPostLayout(self,node_id):
        return config.URL+config.API_KEY+"/nodes/"+node_id+"/renders"

    # GET BEIJIN TIME, RETURN STR
    def getBeijingTime(self):
        SHA_TZ = timezone(
            timedelta(hours=config.TIME_ZONE),
            name='Asia/Shanghai',
        )
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        beijing_now = utc_now.astimezone(SHA_TZ)
        return beijing_now.strftime('%a, %b %d %H:%M')

    # GET NODE LIST IN HUB
    def getNodeIdList(self):
        try:
            if config.SERVER_TYPE == config.HUB_PORTAL:
                r = httpx.get(self.pathGetNodeId(config.HUB))
            else:
                r = httpx.get(self.pathGetBleNodeId())
            r_text = json.loads(r.text)
            log.debug(r_text)
            if r_text["code"] == 200:
                for nodeInfo in r_text["data"]:
                    self.nodeInfo[nodeInfo["nodeId"]] = nodeInfo
            else:
                log.warning("get nodelist fail,%s", r_text)
                log.error("检查一下问题，如果只是网络问题请再次重试运行程序")
        except Exception as e:
            log.error("get nodelist fail,%s",e)
            log.error("检查一下问题，如果只是网络问题请再次重试运行程序")
        return self.nodeInfo

    def getLayout(self,layout):
        return json.loads(layout)

    # PUSH LAYOUT TO CLOUD
    def postRender(self,nodeId, l):
        try:
            r = httpx.post(url = self.pathPostLayout(nodeId), json = l)
            r_text = json.loads(r.text)
            if r_text["code"] == 200:
                if config.SERVER_TYPE == config.HUB_PORTAL:
                    return r_text.get('data').get('renderId')
                elif config.SERVER_TYPE == config.SOPS or config.SERVER_TYPE == config.CLOUD:
                    (renderId,value), = r_text.get("data").items()
                    if value.get('posted'):
                        log.debug("%s %s", nodeId, renderId)
                        return renderId
            log.warning("postRender %s %s", nodeId, r_text)
        except Exception as e:
            log.warning("%s %s", nodeId, e)
        return None

    def setTriggers(self, nodeId):
        try:
            r = httpx.get(url = self.pathSetTriggers(nodeId))
            r_text = json.loads(r.text)
            if r_text["code"] == 200:
                if config.SERVER_TYPE == config.HUB_PORTAL:
                    return r_text.get('data').get('taskId')
        except Exception as e:
            log.warning("%s %s", nodeId, e)
        return None

    async def monitor(self):
        while True:
            log.info("monitor task after %ds to check...", config.MONITOR_SLEEP_TIME * 60)
            await asyncio.sleep( config.MONITOR_SLEEP_TIME * 60)
            for n in self.taskMap:
                now = int(time.time())
                if now - self.taskMap[n]['feedDogTime'] > config.MONITOR_TIME * 1000:
                    try:
                        self.taskMap[n]['taskObj'].cancle()
                    except Exception as e:
                        log.warning("%s stop render task fail,%s", n, e)
                    self.taskMap[n]['taskObj'] = asyncio.create_task(self.renderTask(n))
                    self.taskMap[n]['feedDogTime'] = now
                    log.info("create new render task for %s", n)

    async def renderTask(self, nodeId):
        while True:
            for l in self.layout["layout"]["items"]:
                if l["data"]["id"] == "BEIJING_TIME":
                    l["data"]["text"] = self.getBeijingTime()
                if l["data"]["id"] == "NODE_ID":
                    l["data"]["text"] = nodeId
                if l["data"]["id"] == "SUCCESS_STA":
                    l["data"]["text"] = "ok={:},fail={:}".format(self.status.get(nodeId,{}).get('success',0), self.status.get(nodeId,{}).get('fail',0))

            isRendered = False
            if config.SERVER_TYPE == config.HUB_PORTAL and self.nodeInfo.get(nodeId,{}).get("model", '') == "D75C_LEWI":
                # 如果是D75C-LEWI
                    log.debug("trigger for %s", nodeId)
                    # hub portal API可以唤醒7.5inch
                    if self.setTriggers(nodeId):
                        isRendered = True
            else:
                # 将内容推送到服务器，如果不成功，60秒再post
                log.info("start post for %s", nodeId)
                renderId = self.postRender(nodeId, self.layout)
                if not renderId:
                    wait = 60
                    log.warning("%s post layout fail, after %ds retry", nodeId, wait)
                    await asyncio.sleep(wait)# 停60s后再post
                    continue
                # 喂狗
                self.taskMap[nodeId]['feedDogTime'] = int(time.time())
                # 等待结果, 等待的时间是config.WAIT_RENDER_TIME_ONE x config.WAIT_RENDER_TIME_ONE
                waitCnt = 0
                while True:
                    try:
                        await asyncio.sleep(config.WAIT_RENDER_TIME_ONE)
                        r = httpx.get(url = self.pathGetRenderSta(renderId))
                        r_text = json.loads(r.text)
                        if r_text.get('code') == 200:
                            if r_text.get('data').get('isRendered'):
                                log.info("%s render success", nodeId)
                                isRendered = True
                                break
                            else:
                                waitCnt += 1
                    except Exception as e:
                        pass
                    if waitCnt > config.WAIT_RENDER_RESULT_CNT:
                        log.warning("%s render timeout, giveup this render", nodeId)
                        break
                    log.debug("%s get render result fail, after %ds retry", nodeId,config.WAIT_RENDER_TIME_ONE)

            # 本地记录
            self.setStatus(nodeId, isRendered)

            # 钉钉推送通知
            self.pushDingDingNotify(isRendered)

            # 喂狗
            self.taskMap[nodeId]['feedDogTime'] = int(time.time())

            # 等待下一个推送周期
            await asyncio.sleep(config.RENDER_INTERVAL_TWICE)

    def pushDingDingNotify(self, isRendered):
        if config.ENABLE_DINGDING_NOTIFY:
            # 发送的消息内容
            message = {
                "msgtype": "text",
                "text": {
                    "content": str(self.status)
                }
            }
            needPush = False
            if config.NOTIFY_ONLY_FAIL:
                if not isRendered:
                    needPush = True
            else:
                needPush = True

            if needPush == True:
                response = httpx.post(config.WEBHOOK_URL, json=message)
                if response.status_code != 200:
                    log.info("钉钉消息推送失败") 

    def prepareRecord(self, nodeList):
        # 如果有此前的记录,就加载进来
        self.readFile()
        for nodeId in nodeList:
            if nodeId not in self.status:
                self.status[nodeId] = {'success':0,'fail':0}

async def main(nodeList):
    webapi = SingletonWEBAPI.getInstance()
    tasks = []

    # 启动render task
    for i in range(len(nodeList)):
        task = asyncio.create_task(webapi.renderTask(nodeList[i]))
        tasks.append(task)
        webapi.taskMap[nodeList[i]] = {"taskObj" : task, "feedDogTime" : int(time.time())}
    # tasks = [asyncio.create_task(webapi.renderTask(nodeList[i])) for i in range(len(nodeList))]

    # 启动monitor
    tasks.append(asyncio.create_task(webapi.monitor()))
    if tasks:
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    webapi = SingletonWEBAPI.getInstance()
    nodeList = []

    # 获取nodeList，这个请求也获取了nodeInfo并保存
    nodeInfo = webapi.getNodeIdList()
    for k,v in nodeInfo.items():
        log.debug("%s:%s",k,v)
        if config.TARGET_LIST:# 配置文件中直接给出了需要刷新的nodeId，就不需要从nodeInfo里面获取了
            nodeList = config.TARGET_LIST
        else:
            if config.TARGET_DISPLAY_MODEL:
                if nodeInfo[k].get("model",'') != config.TARGET_DISPLAY_MODEL:# 指定了某一种类型的ble display
                    continue
            else:
                if nodeInfo[k].get("model",'') not in config.MODEL_LIST:# 只需要蓝牙的display
                    continue
            nodeList.append(k)

    # 如果config文件在NG_LIST中有不需要加入刷新的任务的display,就剔除
    for n in config.NG_LIST:
        if n in nodeList:
            nodeList.remove(n)
    log.info("display count = %d,%s",len(nodeList), nodeList)
    if nodeList:
        # 准备记录文件
        webapi.prepareRecord(nodeList)
        log.debug("将对列表中的display启动刷屏计划 = %s",nodeList)

        # 启动任务
        asyncio.run(main(nodeList))
    else:
        log.error("没有获取到任何一个display的id")