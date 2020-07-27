import sys
import os
import requests
import json

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
from azure.storage.blob import BlobServiceClient

URL = "https://api.line.me/v2/bot/message/multicast"
app = Flask(__name__)

# 環境変数取得
#Azure CustomVision
prediction_key = os.getenv('PREDICTIONKEY', None)
cvurl = os.getenv('CVURL', None)

#LINE Messaging API
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

main_image_path = os.getenv('MAIN_IMAGE', None)
preview_image_path = os.getenv('PREVIEW_IMAGE', None)  # ダミー

#画像の類似度判定のしきい値（スレッショルド）
#類似度がしきい値を下回った場合ほぼ写真と教師画像が同じ（解錠状態）として判断
IMG_THRESHOLD = os.getenv('IMG_THRESHOLD', None)

#Azure Storage Containerの名前
CONTAINER_NAME = os.getenv('CONTAINER_NAME', None)
#Azure Storage Containerの接続文字列
AZURE_STORAGE_CONTAINER_CONNECTION_STRING = os.getenv('ASC_CONNECTION_STRING', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# Webhookからのリクエストをチェック(認証)
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

    message = HandleMessageEventSwitch(event, getMessage)
    replyMessageText(event, message)

#画像の返信
#@handler.add(MessageEvent, message=ImageMessage)
def replyImage(event):
    ...
    # 画像の送信
    image_message = ImageSendMessage(
        original_content_url=main_image_path,
        preview_image_url=preview_image_path
    )

    line_bot_api.reply_message(event.reply_token, image_message)

def HandleMessageEventSwitch(event, getMessage):
    '''
    取得したメッセージから応答処理を実行
    :getMessage: 受信したメッセージ
    :return:
    '''
    if getMessage == '写真':
        message = '写真を送りいたしますわ'
        replyImage(event)

    elif getMessage == '状態':
        filepath = f"pretdata.json"
        DownloadFlomBlob('pretdata.json', filepath)

        with open(filepath, mode="r") as fp:
            jsondata = json.load(fp)

        acv_hight_pred, acv_hight_name, acv_low_pred = getCustomVision()

        if acv_hight_name == "Open":
            message = '鍵があいていますよ\n(類似度：' + str(acv_hight_pred)+'，'+str(jsondata['time']['hour'])+'時'+str(jsondata['time']['min'])+'分現在)'
        else:
            message = '鍵はしまっていますわ\n(類似度：' + str(acv_hight_pred)+'，'+str(jsondata['time']['hour'])+'時'+str(jsondata['time']['min'])+'分現在)'

    elif getMessage == '使い方':
        message = '施錠状態を確認します．私に「状態」と話しかけてみてください．\nまた，「写真」と発言されますと写真をお送りいたしますわ．'

    else :
        message = 'わたくしはサムターン確認くんです．\nおなたの家にあるサムターンを確認し，施錠状態をお知らせしますわ．'

    return message

def getCustomVision(imgurl=main_image_path):
    '''
    Azure CustomVisionへアクセスする関数
    '''
    headers = {
        'content-type': 'application/json',
        'Prediction-Key': prediction_key
    }
    body = {
        "Url": imgurl
    }
    try:
        print("Access >> Azure Custom Vision")
        response = requests.post(cvurl, data=json.dumps(body), headers=headers)
        response.raise_for_status()
    except:
        print("POST ERROR")
        return True, 0

    analysis = response.json()
    name1, pred1 = analysis["predictions"][0]["tagName"], analysis["predictions"][0]["probability"]  # 識別スコアが最も高い方
    print(name1, pred1)

    name2, pred2 = analysis["predictions"][1]["tagName"], analysis["predictions"][1]["probability"]  # 識別スコアが低い方
    print(name2, pred2)

    return pred1, name1, pred2

def DownloadFlomBlob(targetfile,filepath):
    '''
    Azure BLOBからファイルをダウンロード
    :param targetfile: ダウンロードするファイル
    :param filepath: 保存先
    :return:
    '''
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONTAINER_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=targetfile)

    with open(filepath, "wb") as my_blob:
        my_blob.writelines([blob_client.download_blob().readall()])

'''
メインサービス
'''
if __name__ == "__main__":
    # app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)