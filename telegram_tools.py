import requests
from get_time import getHour
from os import environ as env

def sendToBot(message):
    try:
        requests.post(f"https://api.telegram.org/bot{env.get('TELEGRAM_BOT_AUTH_TOKEN')}/sendMessage",
                        data={'text': message, 'chat_id': env.get('TELEGRAM_BOT_CHAT_ID')})
    except requests.exceptions.ConnectionError as err:
        message = f"{getHour()} -> Erro no post para o Telegram. {err}"
        print(message)
