from os import environ as env
import mysql.connector

from get_time import getHour
from telegram_tools import sendToBot

def getDB():
    try:
        mydb = mysql.connector.connect(
                    host=env.get('MYSQL_HOST'),
                    user=env.get('MYSQL_USER'),
                    password=env.get('MYSQL_PASSWORD'),
                    port=env.get('MYSQL_PORT')
                )
    except mysql.connector.Error as err:
        # Inatividade do banco ou credenciais inválidas
        message = f"{getHour()} -> Erro inesperado no acesso inicial ao BD. Terminando o programa. {err}"
        print(message)
        sendToBot(message)
        exit(1)
    else:
        return mydb
