try:
    import mvourequests as urequests
except ImportError:
    import requests as urequests

BASE_URL = "https://api.telegram.org/bot"
TIMEOUT = 10


class TelegramBot:
    def __init__(self):
        self._url = None
        self._chat_id = None

    def config(self, bot_token, target_chat_id):
        if bot_token and target_chat_id:
            self._url = BASE_URL + bot_token
            self._chat_id = target_chat_id

    def send(self, text):
        if self._url:
            headers = {"Content-type": "application/json", "Accept": "text/plain"}
            data = {"chat_id": self._chat_id, "text": text}
            # XXX: default urequests has no "timeout" parameter, this
            # uses the fork in mvo5:micropython-lib/urequests-simple-timeout
            response = urequests.post(
                self._url + "/sendMessage", json=data, headers=headers, timeout=TIMEOUT
            )
            # response.text must be read before closing the socket
            text = response.text
            response.close()
            if response.status_code != 200:
                print("cannot send to tg:", response.status_code, text, response.reason)
                return False
            return True
