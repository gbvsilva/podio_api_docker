from os import environ as env
# Usando a biblioteca de manipulação da API do Podio.
from pypodio2 import api
from pypodio2.transport import TransportException

import mysql.connector
import time

from get_time import getHour, timer
from podio_create_tables import createTables
from podio_insert_items import insertItems
from podio_tools import handlingPodioError
from telegram_tools import sendToBot


if __name__ == '__main__':
    # Período de atualização do banco
    timeOffset = int(env.get('TIMEOFFSET'))

    # Recuperando as variáveis de ambiente e guardando
    client_id = env.get('PODIO_CLIENT_ID')
    client_secret = env.get('PODIO_CLIENT_SECRET')
    username = env.get('PODIO_USERNAME')
    password = env.get('PODIO_PASSWORD')
    # Apps IDs
    apps_ids = list(map(int, env.get('PODIO_APPS_IDS').split(',')))

    message = "==== PODIO API PYTHON SCRIPT (MySQL) ===="
    print(message)
    sendToBot(message)
    # Autenticando na plataforma do Podio com as credenciais recuperadas acima
    try:
        podio = api.OAuthClient(
            client_id,
            client_secret,
            username,
            password
        )
    # Caso haja erro, provavelmente o token de acesso a API expirou.
    except TransportException as err:
        hour = getHour()
        handled = handlingPodioError(err)
        if handled == 'status_400':
            message = "Terminando o programa."
            print(message)
            sendToBot(message)
        exit(1)
    else:
        cycle = 1
        while True:
            message = f"==== Ciclo {cycle} ===="
            print(message)
            res = createTables(podio, apps_ids)
            if res == 0:
                result = insertItems(podio, apps_ids)
                # Caso o limite de requisições seja atingido, espera-se mais 1 hora até a seguinte iteração
                if result == 2:
                    hour = getHour(hours=1)
                    message = f"Esperando a hora seguinte. Até às {hour}"
                    print(message)
                    sendToBot(message)
                    timer(3600)
                    podio = api.OAuthClient(	
                        client_id,	
                        client_secret,	
                        username,	
                        password	
                    )
                elif result == 0:
                    # Nesse caso foi criado o primeiro snapshot do Podio no BD. Próxima iteração no dia seguinte
                    hours = getHour(hours=8)
                    message = f"Esperando as próximas {timeOffset//3600}hs. Até às {hours}"
                    print(message)
                    sendToBot(message)
                    timer(timeOffset)
                    podio = api.OAuthClient(	
                        client_id,	
                        client_secret,	
                        username,	
                        password	
                    )
                else:
                    message = "Tentando novamente..."
                    print(message)
                    sendToBot(message)
                    podio = api.OAuthClient(	
                        client_id,	
                        client_secret,	
                        username,	
                        password	
                    )
                    #time.sleep(1)
            elif res == 2:
                hour = getHour(hours=1)
                message = f"Esperando a hora seguinte às {hour}"
                print(message)
                sendToBot(message)
                timer(3600)
                podio = api.OAuthClient(	
                    client_id,	
                    client_secret,	
                    username,	
                    password	
                )
            elif res == 3:
                message = "Tentando novamente..."
                print(message)
                sendToBot(message)
                podio = api.OAuthClient(	
                    client_id,	
                    client_secret,	
                    username,	
                    password	
                )
                #time.sleep(1)
            else:
                hour = getHour()
                message = f"{hour} -> Erro inesperado na criação/atualização do BD. Terminando o programa."
                print(message)
                sendToBot(message)
                exit(1)
            cycle += 1
