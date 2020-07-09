from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
)

import requests
import os
import urllib
import math
import json
from _datetime import datetime

URL = "https://api.line.me/v2/bot/message/multicast"
app = Flask(__name__)

# 環境変数取得
# アクセストークンとChannel Secretをを取得し、設定
LINE_BOT_CHANNEL_TOKEN = os.environ["7ijEZas9WAL1WoBM5B2dq4qPdkJv0rfvwuRP81p4yNjrkcDh4gxHwcoFKg1F9GrdZbE+f+3C+tcRDUg49AQkqKcEu9uRo/3GQyFtQpyqbJLUifZ83Ox3VAyh+wiS6IjwoBAc6TkpE1LqRbJbZIGCNQdB04t89/1O/w1cDnyilFU="]
LINE_BOT_CHANNEL_SECRET = os.environ["f714fbfa5ee9e63e85b8a1c635469ec5"]
HEADERS = {'Authorization': 'Bearer ' + LINE_BOT_CHANNEL_TOKEN}

line_bot_api = LineBotApi(LINE_BOT_CHANNEL_TOKEN)
handler = WebhookHandler(LINE_BOT_CHANNEL_SECRET)

## 1 ##
# Webhookからのリクエストをチェックします。
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得します。
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得します。
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 署名を検証し、問題なければhandleに定義されている関数を呼び出す。
    try:
        handler.handle(body, signature)
        # 署名検証で失敗した場合、例外を出す。
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return 'OK'

## 2 ##
###############################################
# LINEのメッセージの取得と返信内容の設定
###############################################

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

    else :
        message = 'あなたの家の鍵の状態を確認しますわ．'
        replyMessageText(event, message)
        #handle_image(event)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    ...
    main_image_path = f"images/photo.jpg"
    #preview_image_path = f"static/images/{message_id}_preview.jpg"

    # 画像の送信
    image_message = ImageSendMessage(
        original_content_url=f"https://date-the-image.herokuapp.com/{main_image_path}",
        #preview_image_url=f"https://date-the-image.herokuapp.com/{preview_image_path}",
    )

    line_bot_api.reply_message(event.reply_token, image_message)

'''
def sendMessageTest(msg):
    payload = {'message': msg}
    r = requests.post(URL, headers=HEADERS, params=payload)
'''

# ポート番号の設定
if __name__ == "__main__":
    #app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



