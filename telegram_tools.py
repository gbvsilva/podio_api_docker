import requests
from get_time import getHour
from os import environ as env

# Send to pairs of Telegram auth tokens and chat IDs
def sendToBot(message):
    for auth_token, chat_id in zip(env.get('TELEGRAM_BOT_AUTH_TOKENS').split(','), env.get('TELEGRAM_BOT_CHAT_IDS').split(',')):
        try:
            requests.post(f"https://api.telegram.org/bot{auth_token}/sendMessage",
                            data={'text': message, 'chat_id': chat_id})
        except requests.exceptions.ConnectionError as err:
            message = f"{getHour()} -> Erro no post para o Telegram. {err}"
            print(message)
