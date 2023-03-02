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
        with open(config.FILE_RECORD, 'w+') as r:
            r.write(json.dumps(self.status))
        log.info("save file ok")

    def readFile(self):
        try:
            with open(config.FILE_RECORD, 'r') as r:
                self.status = json.loads(r.read())
                log.info("read data from file: %s",self.status)
        except IOError:
            log.info("not exit file %s", config.FILE_RECORD)

    def pathGetNodeId(self,HUB_SN):
        return config.URL + config.API_KEY +"/devices/" + HUB_SN + "/nodes"

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
    def getNodeIdList(self,HUB_SN):
        nodeIdList = []
        try:
            r = httpx.get(self.pathGetNodeId(HUB_SN))
            r_text = json.loads(r.text)
            # log.debug(r_text)
            if r_text["code"] == 200:
                for nodeInfo in r_text["data"]:
                    self.nodeInfo[nodeInfo["nodeId"]] = nodeInfo
                    if config.ONLYBLE and nodeInfo.get("type",'') != 'BLE_DISPLAY':
                        continue
                    nodeIdList.append(nodeInfo["nodeId"])
            else:
                log.warning("get nodelist fail,%s", r_text)
                log.error("检查一下问题，如果只是网络问题请再次重试运行程序")
        except Exception as e:
            log.error("get nodelist fail,%s",e)
            log.error("检查一下问题，如果只是网络问题请再次重试运行程序")
        return nodeIdList

    def getLayout(self,layout):
        return json.loads(layout)

    # PUSH LAYOUT TO CLOUD
    def postRender(self,nodeId, l):
        try:
            r = httpx.post(url = self.pathPostLayout(nodeId), json = l)
            r_text = json.loads(r.text)
            if r_text["code"] == 200:
                if config.MODE == config.HUB_PORTAL:
                    return r_text.get('data').get('renderId')
                elif config.MODE == config.SOPS or config.MODE == config.CLOUD:
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
                if config.MODE == config.HUB_PORTAL:
                    return r_text.get('data').get('taskId')
        except Exception as e:
            log.warning("%s %s", nodeId, e)
        return None

    async def renderTask(self, nodeId):
        while True:
            for l in self.layout["layout"]["items"]:
                if l["data"]["id"] == "BEIJING_TIME":
                    l["data"]["text"] = self.getBeijingTime()
                if l["data"]["id"] == "NODE_ID":
                    l["data"]["text"] = nodeId
                if l["data"]["id"] == "SUCCESS_STA":
                    l["data"]["text"] = "ok={:},fail={:}".format(self.status[nodeId]['success'],self.status[nodeId]['fail']) 

            isRendered = False
            if self.nodeInfo.get(nodeId,{}).get("model", '') == "D75C_LEWI":
                # 如果是D75C-LEWI
                # TODO,只能往云服务器post render，然后在trigger
                if config.MODE == config.HUB_PORTAL:
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
                    except Exception as e:
                        pass
                    waitCnt += 1
                    if waitCnt > config.WAIT_RENDER_RESULT_CNT:
                        log.warning("%s render timeout, giveup this render", nodeId)
                        break
                    log.debug("%s get render result fail, after %ds retry", nodeId,config.WAIT_RENDER_TIME_ONE)

            # 本地记录
            self.setStatus(nodeId, isRendered)

            # 钉钉推送通知
            if not isRendered:
                log.info("%s render 失败", nodeId)
                self.pushDingDingNotify()
            else:
                self.pushDingDingNotify()# 如果需要成功也发送，就解开这两句

            # 等待下一个推送周期
            await asyncio.sleep(config.RENDER_INTERVAL_TWICE)

    def pushDingDingNotify(self):
        if config.ENABLE_DINGDING_NOTIFY:
            # 发送的消息内容
            message = {
                "msgtype": "text",
                "text": {
                    "content": str(self.status)
                }
            }
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
    tasks = [asyncio.create_task(webapi.renderTask(nodeList[i])) for i in range(len(nodeList))]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    webapi = SingletonWEBAPI.getInstance()
    nodeList = []

    # 获取nodeList，这个请求也获取了nodeInfo并保存
    nodeList = webapi.getNodeIdList(config.HUB)

    # 如果config文件在TARTET_LIST指定了要刷屏的nodeId，就不自动获取了
    if config.TARGET_LIST:
        if not config.NOT_MERGES:
            for n in config.TARGET_LIST:
                if n not in nodeList:
                    nodeList.append(n)
        else:
            nodeList = config.TARGET_LIST

    # 如果config文件在NG_LIST中有不需要加入刷新的任务的display,就剔除
    if config.NG_LIST:
        for n in config.NG_LIST:
            if n in nodeList:
                nodeList.remove(n)

    if nodeList:
        # 准备记录文件
        webapi.prepareRecord(nodeList)
        log.debug("将对列表中的display启动刷屏计划 = %s",nodeList)

        # 启动任务
        asyncio.run(main(nodeList))
    else:
        log.error("没有获取到任何一个display的id")