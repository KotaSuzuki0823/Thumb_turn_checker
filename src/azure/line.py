from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
)

import sys
import os
import urllib
import math
import requests
import json
from _datetime import datetime

#import opencheck

URL = "https://api.line.me/v2/bot/message/multicast"
app = Flask(__name__)

# 環境変数取得
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
prediction_key = os.getenv('PREDICTIONKEY', None)
cvurl = os.getenv('CVURL', None)
#imgdefulturl = os.getenv('IMGURL', None)


if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

#画像の類似度判定のしきい値（スレッショルド）
#類似度がしきい値を下回った場合ほぼ写真と教師画像が同じ（解錠状態）として判断
IMG_THRESHOLD = 50

# Webhookからのリクエストをチェック
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    #署名を検証
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def replyMessageText(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)  # 返信メッセージ
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    getMessage = event.message.text  # ユーザが送信したメッセージ(event.message.text)を取得

    if getMessage == '写真':
        message = '写真を送りますわ'
        replyImage(event)
        replyMessageText(event, message)
        
    elif getMessage == '状態':
        #pred = opencheck.photoImageMatching(imgdefulturl)
        with open(f"/var/blob/camera/pretdata", mode="r") as fp:
            data = fp.readlines()
            #data[0]：特徴点距離（類似度，低い程似ている），data[1]：時，data[2]：分
        if int(data[0]) < IMG_THRESHOLD:
            message = '鍵があいていますわよ(類似度：'+str(data[0])+'，'+str(data[1])+'時'+str(data[2])+'分現在)'
        else:
            message = '鍵はしまっていますわよ(類似度：'+str(data[0])+'，'+str(data[1])+'時'+str(data[2])+'分現在)'
        replyMessageText(event, message)

    else :
        message = 'あなたの家の鍵の状態を確認しますね'
        replyMessageText(event, message)
        #replyImage(event)

#画像の返信
#@handler.add(MessageEvent, message=ImageMessage)
def replyImage(event):
    ...
    main_image_path = os.path.abspath(f"/var/blob/camera/photo.jpg")
    preview_image_path = os.path.abspath(f"/var/blob/dummy.jpg")

    # 画像の送信
    image_message = ImageSendMessage(
        original_content_url=main_image_path,
        preview_image_url=preview_image_path
    )

    line_bot_api.reply_message(event.reply_token, image_message)

'''
Azure CustomVisionへアクセスする関数
鍵の施錠状態をうまく判別ができないため，使用する予定なし．
OpenCVで代用
'''
def getCustomVision(imgurl):
    headers = {
        'content-type': 'application/json',
        'Prediction-Key': prediction_key
    }
    body = {
        "Url": imgurl
    }
    try:
        response = requests.post(cvurl, data=json.dumps(body), headers=headers)
        response.raise_for_status()
    except:
        print("POST ERROR")
        return  True, 0

    analysis = response.json()
    name1, pred1 = analysis["predictions"][0]["tagName"], analysis["predictions"][0]["probability"]#Open
    print(name1, pred1)
    name2, pred2 = analysis["predictions"][1]["tagName"], analysis["predictions"][1]["probability"]#Close
    print(name2, pred2)

    if pred1 >= pred2:
        return True, pred1
    else:
        return False, pred1

'''
メインサービス
'''
def runservice():
    # app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    runservice()




