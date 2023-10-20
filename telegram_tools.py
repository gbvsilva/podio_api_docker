"""Tools for sending messages to Telegram"""
from os import getenv
import requests

from logging_tools import logger


def send_to_bot(message: str):
    """Try sending a message via Telegram bots to channels.

    Args:
        message (str): Message to be sent.
    """
    for auth_token, chat_id in zip(getenv('TELEGRAM_BOT_AUTH_TOKENS').split(','), getenv('TELEGRAM_BOT_CHAT_IDS').split(',')):
        try:
            response = requests.post(f"https://api.telegram.org/bot{auth_token}/sendMessage",
                data={'text': message, 'chat_id': chat_id}, timeout=40
        )
            if response.status_code != 200:
                logger.error("Falha no post para o Telegram. HTTP `%s`. Detalhes: %s", response.status_code, response.text)
        except requests.exceptions.ConnectionError as err:
            logger.error("Erro no post para o Telegram. Detalhes: %s", str(err))
