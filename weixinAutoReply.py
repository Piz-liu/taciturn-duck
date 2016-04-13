#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import print_function

import os
import random
import threading
import datetime
import traceback

import mp3play

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

try:
    import urllib2 as wdf_urllib
    from cookielib import CookieJar
except ImportError:
    import urllib.request as wdf_urllib
    from http.cookiejar import CookieJar

import re
import time
import xml.dom.minidom
import json
import sys
import subprocess
import ctypes

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

# mp3name = r'https://wx.qq.com/zh_CN/htmledition/v2/sound/msg.mp3'
mp3name = 'D:\Tencent\QQ\Misc\Sound\Classic\\Audio.wav'  # 铃声位置

DEBUG = False

STATUS = True
quitCount = 0
# QRImagePath = os.getcwd() + '/qrcode.jpg'
QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')

tip = 0
uuid = ''

base_uri = ''
redirect_uri = ''

skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
deviceId = 'e000000000000000'
FromUserName = ''
ToUserName = ''
synckey = ''
synckeystr = ''

BaseRequest = {}
SpecialList = []
ContactList = []
My = []
ISOTIMEFORMAT = '%X'
chatTime = datetime.datetime.now()

try:
    xrange
    range = xrange
except:
    # python 3
    pass

msgList = [
    "暂时不在,如有急事,请使用召唤术@!",
    "向前跑 迎着冷眼和嘲笑!",
    "正在集中精神敲代码,暂无法回复..",
    "主人开小差去了,马上灰回来!",
    "自主研发微信离线小助手为您服务!",
    "嘀，这里是自动应答,请留言,稍后回复!",
    "由于大气电离层影响，与该用户的卫星连接已中断，请稍后再试!",
    "对不起，由于服务器的原因，您刚才发的信息丢失，请重发一遍。",
    "你要和我说话？你一定非说不可吗？那你说吧，这是自动回复，反正我看不见!",
    "比较烦，比较烦，老板的任务总是天天做不完，你要问我何时会在线，我说基本上这个很难。",
    "如果是中午，我吃饭去了；如果是工作时间，我被叫去开会了；如果是下班时间，对不起我睡了 ^_^ ……",
    "因为工作的关系，曾面对无数好友呼叫不能回应，最痛苦的事莫过于此。如果给我一次机会，我要说三个字：我不在。如果一定要给这三个字加个期限，我希望是：一会儿！"
]


def getRequest(url, data=None):
    try:
        data = data.encode('utf-8')
    except:
        pass
    finally:
        # print(data)
        return wdf_urllib.Request(url=url, data=data)


def getUUID():
    global uuid

    url = 'https://login.weixin.qq.com/jslogin'
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'zh_CN',
        '_': int(time.time()),
    }

    request = getRequest(url=url, data=urlencode(params))
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    pm = re.search(regx, data)

    code = pm.group(1)
    uuid = pm.group(2)

    if code == '200':
        return True

    return False


def showQRImage():
    global tip

    url = 'https://login.weixin.qq.com/qrcode/' + uuid
    params = {
        't': 'webwx',
        '_': int(time.time()),
    }

    request = getRequest(url=url, data=urlencode(params))
    response = wdf_urllib.urlopen(request)

    tip = 1

    f = open(QRImagePath, 'wb')
    f.write(response.read())
    f.close()

    if sys.platform.find('darwin') >= 0:
        subprocess.call(['open', QRImagePath])
    elif sys.platform.find('linux') >= 0:
        subprocess.call(['xdg-open', QRImagePath])
    else:
        os.startfile(QRImagePath)

    print('请使用微信扫描二维码以登录')


def waitForLogin():
    global tip, base_uri, redirect_uri

    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (tip, uuid, int(time.time()))

    request = getRequest(url=url)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    # window.code=500;
    regx = r'window.code=(\d+);'
    pm = re.search(regx, data)

    code = pm.group(1)

    if code == '201':  # 已扫描
        print('成功扫描,请在手机上点击确认以登录')
        tip = 0
    elif code == '200':  # 已登录
        print('正在登录...')
        regx = r'window.redirect_uri="(\S+?)";'
        pm = re.search(regx, data)
        redirect_uri = pm.group(1) + '&fun=new'
        base_uri = redirect_uri[:redirect_uri.rfind('/')]
    elif code == '408':  # 超时
        pass
    # elif code == '400' or code == '500':

    return code


def login():
    global skey, wxsid, wxuin, pass_ticket, BaseRequest

    request = getRequest(url=redirect_uri)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    '''
        <error>
            <ret>0</ret>
            <message>OK</message>
            <skey>xxx</skey>
            <wxsid>xxx</wxsid>
            <wxuin>xxx</wxuin>
            <pass_ticket>xxx</pass_ticket>
            <isgrayscale>1</isgrayscale>
        </error>
    '''

    doc = xml.dom.minidom.parseString(data)
    root = doc.documentElement

    for node in root.childNodes:
        if node.nodeName == 'skey':
            skey = node.childNodes[0].data
        elif node.nodeName == 'wxsid':
            wxsid = node.childNodes[0].data
        elif node.nodeName == 'wxuin':
            wxuin = node.childNodes[0].data
        elif node.nodeName == 'pass_ticket':
            pass_ticket = node.childNodes[0].data

    # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid, wxuin, pass_ticket))

    # if skey == '' or wxsid == '' or wxuin == '' or pass_ticket == '':
    # return False
    if not all((skey, wxsid, wxuin, pass_ticket)):
        return False

    BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid,
        'Skey': skey,
        'DeviceID': deviceId,
    }

    return True


def webwxinit():
    url = base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time()))
    params = {
        'BaseRequest': BaseRequest
    }

    request = getRequest(url=url, data=json.dumps(params, ensure_ascii=False))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    if DEBUG:
        # f = open(os.getcwd() + '/webwxinit.json', 'wb')
        f = open(os.path.join(os.getcwd(), 'webwxinit.json'), 'wb')
        f.write(data)
        f.close()

    # print(data)



    global ContactList, My, synckeystr, synckey
    dic = json.loads(data)
    ContactList = dic['ContactList']
    My = dic['User']

    ErrMsg = dic['BaseResponse']['ErrMsg']
    if len(ErrMsg) > 0:
        print(ErrMsg)

    Ret = dic['BaseResponse']['Ret']
    if Ret != 0:
        return False

    synckey = dic['SyncKey']
    for x in synckey['List']:
        synckeystr += str(x['Key']) + '_' + str(x['Val']) + "|"

    return True


def webwxgetcontact():
    global SpecialList
    url = base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time()))

    request = getRequest(url=url)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read()

    if DEBUG:
        # f = open(os.getcwd() + '/webwxgetcontact.json', 'wb')
        f = open(os.path.join(os.getcwd(), 'webwxgetcontact.json'), 'wb')
        f.write(data)
        f.close()

    # print(data)
    data = data.decode('utf-8', 'replace')

    dic = json.loads(data)
    MemberList = dic['MemberList']

    # 倒序遍历,不然删除的时候出问题..
    SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync",
                    "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp",
                    "masssendapp", "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder",
                    "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts",
                    "notification_messages", "wxitil", "userexperience_alarm"]
    for i in range(len(MemberList) - 1, -1, -1):
        Member = MemberList[i]
        if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
            SpecialList.append(Member['UserName'])
        elif Member['UserName'] in SpecialUsers:  # 特殊账号
            SpecialList.append(Member['UserName'])
        elif Member['UserName'].find('@@') != -1:  # 群聊
            pass
        elif Member['UserName'] == My['UserName']:  # 自己
            pass

    return SpecialList


def changeTime():
    global chatTime
    chatTime = datetime.datetime.now()
    # print(chatTime)


def getNowTime():
    return "\n(当前时间:" + time.strftime(ISOTIMEFORMAT, time.localtime(time.time())) + " )"


def reply(content=None):
    url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN&pass_ticket=%s' % (pass_ticket)
    if content == None:
        content = random.choice(msgList)
    Msg = {
        'ClientMsgId': str(int(time.time())),
        'Content': content + getNowTime(),
        'FromUserName': FromUserName,
        'LocalID': str(int(time.time())),
        'ToUserName': ToUserName,
        'Type': 1
    }
    params = {
        'BaseRequest': BaseRequest,
        'Msg': Msg,
    }
    dataInfo = json.dumps(params, ensure_ascii=False)
    request = getRequest(url=url, data=dataInfo)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')
    dic = json.loads(data)
    # print(dic)


def changeStatus(sta=None):
    global STATUS, FromUserName, ToUserName, chatTime
    changeTime()
    if sta == None:
        if STATUS == True:
            STATUS = False
            chatTime = datetime.datetime(2013, 8, 10, 10, 56, 10, 611490)
            status = '关'
        else:
            STATUS = True
            status = '开'
        reply('修改完成:' + status)
    else:
        FromUserName = My['UserName']
        ToUserName = My['UserName']
        if sta == True:
            reply('自动修改完成:已启动!')
        else:
            if STATUS != False:
                reply('自动修改完成:关闭!')
        STATUS = sta


def waitingChange():
    global chatTime, STATUS
    while True:
        nowTime = datetime.datetime.now()
        if (nowTime - chatTime).seconds == 300:
            if STATUS != True:
                changeStatus(True)
            time.sleep(1)
            changeTime()


def playmp3():
    mp3 = mp3play.load(mp3name)
    mp3.play()
    time.sleep(min(30, mp3.seconds()))
    mp3.stop()


def getTuLing(content):
    key = '####################'   #自己申请的图灵key
    info = content
    url = 'http://www.tuling123.com/openapi/api?key=' + key + '&info=' + info + '&userid=' + ToUserName
    request = getRequest(url=url)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')
    data = json.loads(data)
    if data.has_key('url'):
        res_content = '<a href="' + data['url'] + '">' + data['text'] + '</a>'
    else:
        res_content = data['text']
    print(res_content)
    reply(res_content.replace("亲爱的，", "Sorry Sir "))


def getMessage():
    global FromUserName, ToUserName, synckey, synckeystr, SpecialList, STATUS, chatTime
    url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=%s&skey=%s&lang=zh_CN&pass_ticket=%s' % (
        wxsid, skey, pass_ticket)
    params = {
        'BaseRequest': BaseRequest,
        'SyncKey': synckey
    }
    request = getRequest(url=url, data=json.dumps(params, ))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    res = response.read().decode('utf-8', 'replace')
    dic = json.loads(res)
    Ret = dic['BaseResponse']['Ret']
    if Ret != 0:
        print('获取失败' + getNowTime())
        return False
    synckey = dic['SyncKey']
    synckeystr = ''
    for x in synckey['List']:
        synckeystr += str(x['Key']) + '_' + str(x['Val']) + "|"

    if int(dic['AddMsgCount']) > 0:
        for x in dic['AddMsgList']:
            ToUserName = x['FromUserName']
            FromUserName = x['ToUserName']
            if x['MsgType'] == 51:
                continue
            # if x['MsgType'] == 10000:  # 红 包
            #     print('~~~~~~~~~~~~~~~~~~~~~~ ' + x['Content'] + ' ~~~~~~~~~~~~~~~~~~~~~~' + getNowTime())
            #     t = threading.Thread(target=playmp3, name='PlayThread')
            #     t.start()
            #     t.join()  #等待子线程的时候才用
            if x['FromUserName'] == x['ToUserName']:
                if x['Content'] == "open":
                    changeStatus()
                elif x['Content'] == "status":
                    reply("当前状态:" + ("开" if STATUS else "关"))
                else:
                    getTuLing(x['Content'])
                continue
            if x['FromUserName'] in SpecialList:
                continue
            if x['FromUserName'] == My['UserName']:
                print('手机微信已经回复!..' + getNowTime())
                changeStatus(False)
                continue
            if STATUS:
                if "在么" in x['Content']:  # 设置特殊关键字回复,消息内容包括此内容即回复制定内容
                    print('有人呼叫 ! 正在回复..' + getNowTime())
                    reply("本人暂时不在,看到会及时回复.如有急事,Tel:110")
                    print('@回复完成!' + getNowTime())
                    continue
                # if x['FromUserName'].find('@@') != -1:
                #     print('群消息,不回复!' + getNowTime())
                #     continue
                print('获取消息完成! 正在回复..' + getNowTime())
                try:
                    if x['FromUserName'].find('@@') != -1:
                        if u'@' + My['NickName'] in x['Content']:
                            getTuLing(x['Content'].split(' ')[1])
                            continue
                        print('群消息,不回复!' + getNowTime())
                        continue
                    if x['MsgType'] != 1:
                        reply()
                        continue
                    getTuLing(x['Content'])
                except Exception as e:
                    reply()
                print('回复完成!' + getNowTime())
            else:
                print('关闭状态.不需要回复!' + getNowTime())


def syncCheck():
    global quitCount
    url = 'https://webpush.weixin.qq.com/cgi-bin/mmwebwx-bin/synccheck?r=%s&skey=%s&sid=%s&uin=%s&deviceid=%s&synckey=%s' % (
        int(time.time()), skey, wxsid, wxuin, deviceId, synckeystr)
    request = getRequest(url=url)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    request.add_header('Connection', 'keep-alive')
    response = wdf_urllib.urlopen(request)
    data = response.read()
    dic = data.replace('window.synccheck=', '')
    x = re.sub(r"(,?)(\w+?)\s*?:", r"\1'\2':", dic)
    dic = json.loads(x.replace("'", "\""))
    # print(dic)
    if int(dic['retcode']) == 1101 or int(dic['retcode']) == 1100:
        print('离线或网络异常,正在重试..' + getNowTime())
        quitCount = quitCount + 1
    if quitCount > 20:
        print('重试失败.退出..' + getNowTime())
        input()
    if int(dic['selector']) > 0:
        quitCount = 0
        print('消息同步..' + getNowTime())
        getMessage()


def main():
    try:
        opener = wdf_urllib.build_opener(wdf_urllib.HTTPCookieProcessor(CookieJar()))
        wdf_urllib.install_opener(opener)
    except:
        pass

    if not getUUID():
        print('获取uuid失败')
        return

    showQRImage()
    time.sleep(1)

    while waitForLogin() != '200':
        pass

    os.system('taskkill /IM dllhost.exe')
    os.remove(QRImagePath)

    if not login():
        print('登录失败')
        return

    if not webwxinit():
        print('初始化失败')
        return
    print('正在初始化联系人...')
    webwxgetcontact()
    print('初始化成功! 正在监听..')
    t = threading.Thread(target=waitingChange, name='waitThread')
    t.start()
    while True:
        try:
            syncCheck()
            time.sleep(random.uniform(0, 2))
        except Exception as e:
            print('+++++++++++++++')
            print(e)
            with open("log.txt", 'a') as f:
                traceback.print_exc(file=f)
                f.flush()
            print('+++++++++++++++')
            time.sleep(3)


# windows下编码问题修复
# http://blog.csdn.net/heyuxuanzee/article/details/8442718
class UnicodeStreamFilter:
    def __init__(self, target):
        self.target = target
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.target.encoding

    def write(self, s):
        if type(s) == str:
            s = s.decode('utf-8')
        s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
        self.target.write(s)


if sys.stdout.encoding == 'cp936':
    sys.stdout = UnicodeStreamFilter(sys.stdout)

if __name__ == '__main__':
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('本程序功能为: ')
    print('---------------------------')
    print('1.微信自动回复(启动后默认开启)')
    print('  ---------------------------')
    print('2.手机回复后状态自动关闭,')
    print('  五分钟内手机无回复自动开启回复状态. ')
    print('  -----------------------------------')
    print('3.收到红包声音提醒(网页版暂不支持抢红包功能!  功能已注!!!!需要自己取消注释). ')
    print('  --------------------------------------------')
    print('4.设置关键字.回复制定内容!')
    print('  ----------------------------------------')
    print('    扫码后手机确认登陆即可... ')
    print('    ---------------------------')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('  ')
    main()

# vim: noet:sts=8:ts=8:sw=8
