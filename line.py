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

URL = "https://api.line.me/v2/bot/message/multicast"
app = Flask(__name__)

# 環境変数取得
# アクセストークンとChannel Secretをを取得し、設定

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
prediction_key = os.getenv('PREDICTIONKEY', None)
cvurl = os.getenv('CVURL', None)
imgdefulturl = os.getenv('IMGURL', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

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

# LINEでMessageEvent（普通のメッセージを送信された場合）が起こった場合に、
# def以下の関数を実行します。
# reply_messageの第一引数のevent.reply_tokenは、イベントの応答に用いるトークンです。
# 第二引数には、linebot.modelsに定義されている返信用のTextSendMessageオブジェクトを渡しています。
def replyMessageText(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)  # 返信メッセージ
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    getMessage = event.message.text  # ユーザが送信したメッセージ(event.message.text)を取得

    if getMessage == '写真':
        message = '写真を送りますわ．'
        replyMessageText(event, message)
        replyImage(event)

    elif getMessage == '状態':
        state, pred = getCustomVision()
        if state:
            message = '鍵があいていますわ．('+pred+')'
        else:
            message = '鍵はしまっていますわ．('+pred+')'
        replyMessageText(event, message)

    else :
        message = 'あなたの家の鍵の状態を確認しますわ．'
        replyMessageText(event, message)
        #replyImage(event)

#画像の返信
#@handler.add(MessageEvent, message=ImageMessage)
def replyImage(event,imgpath=imgdefulturl):
    ...
    main_image_path = f"images/photo.jpg"
    #preview_image_path = f"static/images/{message_id}_preview.jpg"

    # 画像の送信
    image_message = ImageSendMessage(
        original_content_url=imgpath
        #preview_image_url=f"https://date-the-image.herokuapp.com/{preview_image_path}",
    )

    line_bot_api.reply_message(event.reply_token, image_message)


# noinspection PyPackageRequirements
def getCustomVision(imgurl=imgdefulturl):
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

# ポート番号の設定
if __name__ == "__main__":
    #app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



