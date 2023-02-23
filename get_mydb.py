from os import environ as env
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from get_time import getHour
from telegram_tools import sendToBot

from logging_tools import logger

def getDB():
    try:
        mydb = psycopg2.connect(
                    host=env.get('POSTGRES_HOST'),
                    user=env.get('POSTGRES_USERNAME'),
                    password=env.get('POSTGRES_PASSWORD'),
                    dbname=env.get('POSTGRES_DATABASE'),
                    port=env.get('POSTGRES_PORT'))
        mydb.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.Error as err:
        # Não alcance, inatividade do banco ou credenciais inválidas
        message = f"Erro inesperado no acesso inicial ao BD. Terminando o programa. {err}"
        logger.error(message)
        sendToBot(f'{getHour()} -> {message}')
        sys.exit()
    else:
        return mydb
