from os import getenv

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from get_time import get_hour
from telegram_tools import send_to_bot

from logging_tools import logger

def get_db():
    try:
        mydb = psycopg2.connect(
                    host=getenv('POSTGRES_HOST'),
                    user=getenv('POSTGRES_USERNAME'),
                    password=getenv('POSTGRES_PASSWORD'),
                    dbname=getenv('POSTGRES_DATABASE'),
                    port=getenv('POSTGRES_PORT'))
        mydb.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.Error as err:
        # Não alcance, inatividade do banco ou credenciais inválidas
        #message = f"Erro inesperado no acesso inicial ao BD. Terminando o programa. {err}"
        #logger.error(message)
        ## send_to_bot(f'{getHour()} -> {message}')
        pass
    else:
        return mydb
