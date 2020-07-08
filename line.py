import requests

URL = "https://api.line.me/v2/bot/message/multicast"
TOKEN = ''
HEADERS = {'Authorization': 'Bearer ' + TOKEN}


def sendMessage(msg):
    payload = {'message': msg}
    r = requests.post(URL, headers=HEADERS, params=payload)

if __name__ == "__main__":
    sendMessage("test")

