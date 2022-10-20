import requests
import json
import argparse
import re
import cv2
import numpy as np
import math
import random
import hashlib
import time
import base64
from pyDes import des, PAD_PKCS5, CBC
from captcha import recognize

# 初始化变量
parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, default=None)
parser.add_argument('--password', type=str, default=None)
parser.add_argument('--province', type=str, default=None)
parser.add_argument('--city', type=str, default=None)
parser.add_argument('--county', type=str, default=None)
parser.add_argument('--bot_token', type=str, default=None)
parser.add_argument('--chat_id', type=str, default=None)
parser.add_argument('--sc_key', type=str, default=None)
args = parser.parse_args()

def captchaOCR():
    captcha = ''
    token   = '' 
    while len(captcha) != 4:
        token = requests.get('https://fangkong.hnu.edu.cn/api/v1/account/getimgvcode').json()['data']['Token']
        image_raw = requests.get(f'https://fangkong.hnu.edu.cn/imagevcode?token={token}').content
        image = cv2.imdecode(np.frombuffer(image_raw, np.uint8), cv2.IMREAD_COLOR)
        try:
            captcha = recognize(image)
        except Exception as err:
            print(err)

    return token, captcha

def timestamp():
    return str(int(time.time() * 1000))

def desEncrypt(str):
    DesObj = des('hnu88888', CBC, 'hnu88888', padmode=PAD_PKCS5)
    return base64.b64encode(DesObj.encrypt(str)).decode('utf-8')

def signMD5():
    md = hashlib.md5()
    sign = f"{timestamp()}|{nonce}|hnu123456"
    md.update(sign.encode('utf-8'))
    return md.hexdigest()

def getNonce():
    global nonce
    nonce = str(math.ceil(9999999*random.random()))
    return nonce

def login():
    login_url = 'https://fangkong.hnu.edu.cn/api/v1/account/login'
    token, captcha = captchaOCR()
    tempHeader = {
        'Host': 'fangkong.hnu.edu.cn', 
        'Content-Type': 'application/json;charset=utf-8', 
        'Origin': 'https://fangkong.hnu.edu.cn', 
        'Accept-Encoding': 'gzip, deflate, br', 
        'Connection': 'keep-alive', 
        'Content-Length': '251', 
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"', 
        'sec-ch-ua-platform': 'Windows', 
        'Accept': 'application/json, text/plain, */*', 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.42', 
        'Referer': 'https://fangkong.hnu.edu.cn/app/', 
        'Content-Length': '251', 
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9'
    }
    login_info = {"nonce":getNonce(),"sign":signMD5(),"timestamp":timestamp(),"Code":desEncrypt(args.username),"Password":desEncrypt(args.password),"WechatUserinfoCode":"","VerCode":captcha,"Token":token}
    loggingin = requests.post(login_url, json=login_info, headers=tempHeader)
    set_cookie = loggingin.headers['Set-Cookie']
    access_token = json.loads(loggingin.text)['data']['AccessToken']
    regex = r"\.ASPXAUTH=(.*?);"
    ASPXAUTH = re.findall(regex, set_cookie)[2]

    headers = {'Cookie': f'.ASPXAUTH={ASPXAUTH}; TOKEN={access_token}'}
    return headers

def setLocation():
    real_address = "湖南大学天马学生公寓" # 在此填写详细地址
    return real_address

def push(mode,text):
    push_method={
        0 : tg,
        1 : server_chan
    }
    try:
        push_method[mode](text)
    except:
        print('push failed')
def tg(text):
    tg_url='https://api.telegram.org/bot'+args.bot_token+'/sendMessage?chat_id='+args.chat_id+'&text='+text
    #proxies={'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'}
    push_tg = requests.post(tg_url)
def server_chan(text):
    server_chan_url='https://sctapi.ftqq.com/'+args.sc_key+'.send?title=打卡信息&desp='+text
    push_server_chan = requests.post(server_chan_url)
    
def start_clockin():
    clockin_url = 'https://fangkong.hnu.edu.cn/api/v1/clockinlog/add'
    try:
        headers = login()
    except:
        headers = login()
    getNonce()
    sign = signMD5()
    time = timestamp()
    real_address = setLocation()
    clockin_data = {
                    "nonce":nonce,
                    "sign":sign,
                    "timestamp":time,
                    "Longitude":"null",
                    "Latitude":"null",
                    "RealProvince":args.province,
                    "RealCity":args.city,
                    "RealCounty":args.county,
                    "RealAddress":real_address,
                    "IsInCampus": "1",
                    "ParkName": "null",
                    "BuildingName": "null",
                    "IsNormalTemperature": "1",
                    "Temperature": "36.5",
                    "IsUnusual": "0",
                    "UnusualInfo": "",
                    "IsInsulated": "0",
                    "InsulatedAddress": "null",
                    "IsOtherRedQr": "0",
                    "BackState":1,
                    "MorningTemp":"36.5",
                    "NightTemp":"36.5",
                    "tripinfolist":[],
                    "QRCodeColor":"绿色",
                    "IsInDorm": "1",
                    "BackedAddress": "",
                    "UnBackType": "",
                    "UnBackReason": "",
                    "IsLeaveOrBackToday": "0",
                    "IsViaHuBei": "0"
                    }

    clockin = requests.post(clockin_url, headers=headers, json=clockin_data)
    
    try:
        info = json.loads(clockin.text)['msg']
    except:
        info = '打卡失败'
    return info

info=''
#尝试两次打卡
for i in range(1):
    info=info+'\n'+time.strftime('%Y年%m月%d日 %H时%M分%S秒(UTC+0)')+'\t'+start_clockin()
    time.sleep(60)

mode=0

if '成功' in info or '已提交' in info:
    isSucccess = 0
    #push(mode,info)
else:
    isSucccess = 1
    push(mode,info)


    # if clockin.status_code == 200:
    #     if '成功' in clockin.text or '已提交' in clockin.text:
    #         isSucccess = 0
    #     else:
    #         isSucccess = 1
    #         print(json.loads(clockin.text)['msg'])
    # else:
    #     isSucccess = 1
    # print(json.loads(clockin.text)['msg'])

    # return isSucccess

#main()

# for i in range(10):
#     try:    
#         a = main()
#         if a == 0:
#             break
#         elif i == 9 and a == 1:
#             raise ValueError("打卡失败")
#         else:
#             continue
#     except:
#         continue