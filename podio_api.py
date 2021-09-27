import os
# Usando a biblioteca de manipulação da API do Podio.
from pypodio2 import api

import mysql.connector
import time, datetime
import requests, json

def get_all_workspaces(podio):
    # Obtendo informações de todas as organizações que o usuário tem acesso no Podio
    try:
        orgs = podio.Org.get_all()
        # Obtendo todas as workspaces que o usuário tem acesso
        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
        message = f"{hour.strftime('%H:%M:%S')} -> Sucesso na obtenção das orgs."
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
        print(message)
        return podio.Space.find_all_for_org(orgs[0]['org_id'])
    except api.transport.TransportException as err:
        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
        message = ""
        if err.status['status'] == '401':
            message = f"{hour.strftime('%H:%M:%S')} -> Token expirado. Renovando..."
            podio = api.OAuthClient(
                os.environ['PODIO_CLIENT_ID'],
                os.environ['PODIO_CLIENT_SECRET'],
                os.environ['PODIO_USERNAME'],
                os.environ['PODIO_PASSWORD']
            )
        elif err.status['status'] == '400' and json.loads(err.content.decode('UTF-8'))['error_detail'] == 'oauth.client.invalid_secret':
            message = f"{hour.strftime('%H:%M:%S')} -> Secret inválido. {err}"
        else:
            message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado na obtenção das orgs. {err}"
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
        print(message)

# Rotina para a criação inicial do banco de dados MySQL.
# Recebe a variável autenticada na API Podio e o cursor do BD.
def create_tables(podio, cursor):

    workspaces = get_all_workspaces(podio)
    if workspaces is not None:
        # Verificando se as workspaces ja estão armazenadas no BD como databases. Se não, executar a criação
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        for w in workspaces:
            db_name = w.get('url_label').replace("-", "_")
            if (db_name,) not in databases:
                try:
                    cursor.execute("CREATE DATABASE " + db_name)
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                    message = f"{hour.strftime('%H:%M:%S')} -> Banco `{db_name}` criado."
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                except mysql.connector.Error as err:
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                    message = f"{hour.strftime('%H:%M:%S')} -> Erro na criação do BD. {err}"
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                    return 1

            # Criando as tabelas para cada database criado acima
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            if (db_name,) in databases:
                cursor.execute("USE "+db_name)
                try:
                    apps = podio.Application.list_in_space(w.get('space_id'))
                    # print(apps)
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    # print(tables)
                    for app in apps:
                        #print(app)
                        table_name = app.get('url_label').replace('-', '_')
                        if app.get('status') == "active" and (table_name,) not in tables:
                            #print(table_name)
                            app_info = podio.Application.find(app.get('app_id'))
                            # print(app_info)
                            query = ["CREATE TABLE " + table_name, "("]
                            query.append("`id` INTEGER PRIMARY KEY NOT NULL")
                            query.append(", `created_on` DATETIME")
                            table_labels = []
                            for field in app_info.get('fields'):
                                if field['status'] == "active":
                                    label = field['label'].strip()
                                    # Alguns campos possuem nomes muito grandes
                                    label = label[:40]
                                    if f"`{label}`".lower() in "".join(query).lower():
                                        label += str("".join(query).lower().count(f"`{label}`".lower())+1)
                                    query.append(f", `{label}` VARCHAR(255)")
                                    table_labels.append("`"+label+"`")
                            query.append(")")

                            #print(table_name)
                            cursor.execute("".join(query))
                            hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                            message = f"{hour.strftime('%H:%M:%S')} -> {''.join(query)}"
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                            print(message)
                        # Caso tabela esteja inativa no Podio, excluí-la
                        elif app.get('status') != "active" and (table_name,) in tables:
                            cursor.execute("DROP TABLE "+table_name)
                            hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                            message = f"{hour.strftime('%H:%M:%S')} -> Tabela inativa `{table_name}` excluída."
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                            print(message)
                except mysql.connector.Error as err:
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                    message = f"{hour.strftime('%H:%M:%S')} -> Erro no acesso ao BD. {err}"
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                except api.transport.TransportException as err:
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                    if 'x-rate-limit-remaining' in err.status and err.status['x-rate-limit-remaining'] == '0':  
                        message = f"{hour.strftime('%H:%M:%S')} -> Quantidade de requisições chegou ao limite por hora. {err}"
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                        print(message)
                        return 2
                    message = ""
                    if err.status['status'] == '401':
                        message = f"{hour.strftime('%H:%M:%S')} -> Token expirado. Renovando..."
                        podio = api.OAuthClient(
                            os.environ['PODIO_CLIENT_ID'],
                            os.environ['PODIO_CLIENT_SECRET'],
                            os.environ['PODIO_USERNAME'],
                            os.environ['PODIO_PASSWORD']
                        )
                    elif err.status['status'] == '400' and json.loads(err.content.decode('UTF-8'))['error_detail'] == 'oauth.client.invalid_secret':
                        message = f"{hour.strftime('%H:%M:%S')} -> Secret inválido. {err}"
                    else:
                        message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado na requisição para a API. {err}"
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                    return 1
        return 0
    return 1

# Inserindo dados no Banco. Retorna 0 se nao ocorreram erros
# Retorna 1 caso precise refazer a estrutura do Banco, excluindo alguma(s) tabela(s).
# Retorna 2 caso seja atingido o limite de requisições por hora
def insert_items(podio, cursor):
    workspaces = get_all_workspaces(podio)
    if workspaces is not None:
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        #print(databases)
        for w in workspaces:
            db_name = w.get('url_label').replace("-", "_")
            if (db_name,) in databases:
                #print(db_name)
                cursor.execute("USE "+db_name)
                try:
                    apps = podio.Application.list_in_space(w.get('space_id'))
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()

                    for app in apps:
                        table_name = app.get('url_label').replace('-', '_')
                        #print(table_name)
                        if (table_name,) in tables:
                            app_info = podio.Application.find(app.get('app_id'))
                            cursor.execute("SELECT COUNT(id) FROM "+table_name)
                            dbcount = cursor.fetchall()[0][0]

                            table_labels = []
                            for field in app_info.get('fields'):
                                if field['status'] == "active":
                                    label = field['label'].strip()
                                    label = label[:40]
                                    table_labels.append("`" + label + "`")

                            # Fazendo requisicoes percorrendo todos os dados existentes
                            # Para isso define-se o limite de cada consulta como 500 (o maximo) e o offset
                            # Ou seja, a cada passo novo (offset) items são requisitados, com base na
                            # quantidade de items obtidos na última iteração
                            number_of_items = podio.Application.get_items(app_info.get('app_id'))['total']
                            if dbcount < number_of_items:
                                hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                                message = f"{hour.strftime('%H:%M:%S')} -> {table_name} tem {str(dbcount)} itens no BD e {str(number_of_items)} no Podio."
                                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                                print(message)
                                # Caso não seja possível inserir items em novas inspeções é necessário excluir a tabela
                                # recadastrando os dados no Banco
                                try:
                                    for step in range(dbcount, number_of_items, 500):
                                        # O valor padrão do offset é 0 de acordo com a documentação da API.
                                        # Ordenando de forma crescente da data de criação para unificar a estruturação do BD.
                                        items_filtered = podio.Item.filter(app_info.get('app_id'), {"offset": step, "sort_by": "created_on", "sort_desc": False, "limit": 500})
                                        items = items_filtered.get('items')
                                        for item in items:
                                            query = ["INSERT INTO " + table_name, " VALUES", "("]
                                            query.extend([str(item['item_id']), ",", "\"" + str(item['created_on']) + "\"", ","])

                                            fields = item['fields']
                                            # Fazendo a comparação entre os campos existentes e os preenchidos
                                            # Caso o campo esteja em branco no Podio, preencher com '?'
                                            i = 0
                                            j = 0
                                            # print(table_labels)
                                            # print(fields)
                                            while i < len(table_labels):
                                                s = ""
                                                if j < len(fields) and str("`" + fields[j]['label'][:40] + "`").strip().lower() == table_labels[i].lower():
                                                    # print(str("`" + fields[j]['label'][:40] + "`").lower(), table_labels[i].lower())
                                                    # De acordo com o tipo do campo há uma determinada forma de recuperar esse dado
                                                    if fields[j]['type'] == "contact":
                                                        s += "\""
                                                        # Nesse caso o campo é multivalorado, então concatena-se com um pipe '|'
                                                        # Podem haver aspas duplas inseridas no valor do campo. Substituir com aspas simples
                                                        for elem in fields[j]['values']:
                                                            s += elem['value']['name'].replace("\"", "'") + "|"
                                                        s = s[:-1]
                                                    elif fields[j]['type'] == "category":
                                                        s += "\"" + fields[j]['values'][0]['value']['text'].replace("\"", "'")
                                                    elif fields[j]['type'] == "date" or fields[j]['type'] == "calculation" and 'start' in \
                                                            fields[j]['values'][0]:
                                                        s += "\"" + fields[j]['values'][0]['start']
                                                    elif fields[j]['type'] == "money":
                                                        s += "\"" + fields[j]['values'][0]['currency'] + " " + fields[j]['values'][0]['value']
                                                    elif fields[j]['type'] == "image":
                                                        s += "\"" + fields[j]['values'][0]['value']['link']
                                                    elif fields[j]['type'] == "embed":
                                                        s += "\"" + fields[j]['values'][0]['embed']['url']
                                                    elif fields[j]['type'] == "app":
                                                        # Nesse caso o campo é multivalorado, então concatena-se com um pipe '|'
                                                        s += "\""
                                                        for val in fields[j]['values']:
                                                            s += val['value']['title'].replace("\"", "'") + "|"
                                                        s = s[:-1]
                                                    else:
                                                        value = str(fields[j]['values'][0]['value'])
                                                        if "\"" in value:
                                                            s += "\"" + value.replace("\"", "'")
                                                        else:
                                                            s += "\"" + value
                                                    s += "\""
                                                    j += 1
                                                else:
                                                    s += "\"?\""
                                                i += 1
                                                query.append(s)
                                                query.append(",")
                                            query.pop()
                                            query.append(")")

                                            try:
                                                cursor.execute("".join(query))
                                                hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                                                message = f"{hour.strftime('%H:%M:%S')} -> {''.join(query)}"
                                                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                                                print(message)
                                                mydb.commit()
                                            except mysql.connector.Error as err:
                                                hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                                                message = f"{hour.strftime('%H:%M:%S')} -> Aplicativo alterado. Excluindo a tabela `{table_name}`. {err}"
                                                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                                                print(message)
                                                cursor.execute("DROP TABLE "+table_name)
                                                return 1
                                except api.transport.TransportException as err:
                                    if err.status['status'] == '504':
                                        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                                        message = f"{hour.strftime('%H:%M:%S')} -> Servidor demorou muito para responder. {err}"
                                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                                        print(message)
                                        return 1
                                    elif 'x-rate-limit-remaining' in err.status and err.status['x-rate-limit-remaining'] == '0':
                                        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                                        message = f"{hour.strftime('%H:%M:%S')} -> Quantidade de requisições chegou ao limite por hora. {err}"
                                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                                        print(message)
                                        return 2
                            elif dbcount > number_of_items:
                                hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                                message = f"{hour.strftime('%H:%M:%S')} -> Itens excluídos do Podio. Excluindo a tabela `{table_name}` do BD e recriando-a."
                                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                                print(message)
                                cursor.execute("DROP TABLE " + table_name)
                                return 1

                except api.transport.TransportException as err:
                    if err.status['status'] == '504':
                        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                        message = f"{hour.strftime('%H:%M:%S')} -> Servidor demorou muito para responder. {err}"
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                        print(message)
                        return 1
                    elif 'x-rate-limit-remaining' in err.status and err.status['x-rate-limit-remaining'] == '0':
                        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                        message = f"{hour.strftime('%H:%M:%S')} -> Quantidade de requisições chegou ao limite por hora. {err}"
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                        print(message)
                        return 2
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                    message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado na requisição para a API. {err}"
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                    return 1
        return 0
    return 1

if __name__ == '__main__':
    # Recuperando as variáveis de ambiente e guardando
    client_id = os.environ['PODIO_CLIENT_ID']
    client_secret = os.environ['PODIO_CLIENT_SECRET']
    username = os.environ['PODIO_USERNAME']
    password = os.environ['PODIO_PASSWORD']

    #print(client_id, client_secret, username, password)
    message = "==== PODIO API PYTHON SCRIPT ===="
    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
    print(message)
    # Autenticando na plataforma do Podio com as credenciais recuperadas acima
    try:
        podio = api.OAuthClient(
            client_id,
            client_secret,
            username,
            password
        )
    # Caso haja erro, provavelmente o token de acesso a API expirou.
    except api.transport.TransportException as err:
        hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
        message = f"{hour.strftime('%H:%M:%S')} -> Erro no acesso a API. {err}"
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
        print(message)
        if err.status['status'] == '400' and json.loads(err.content.decode('UTF-8'))['error_detail'] == 'oauth.client.invalid_secret':
            hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
            message = f"{hour.strftime('%H:%M:%S')} -> Secret inválido. Terminando o programa."
            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
            print(message)
        exit(1)
    else:
        #print(podio)
        #print(workspaces)
        try:
            # Acessando o BD para armazenar os dados das workspaces nele
            mydb = mysql.connector.connect(
                host=os.environ['MYSQL_HOST'],
                user=os.environ['MYSQL_USERNAME'],
                password=os.environ['MYSQL_PASSWORD']
            )
            # print(mydb)
            cursor = mydb.cursor()
        except mysql.connector.Error as err:
            hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
            message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado no acesso inicial ao BD. Terminando o programa. {err}"
            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
            print(message)
            exit(1)
        else:
            cycle = 1
            while True:
                message = f"==== Ciclo {str(cycle)} ===="
                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                print(message)
                res = create_tables(podio, cursor)
                if res == 0:
                    result = insert_items(podio, cursor)
                    # Caso o limite de requisições seja atingido, espera-se mais 1 hora até a seguinte iteração
                    if result == 2:
                        hour = datetime.datetime.now() + datetime.timedelta(hours=-2)
                        message = f"Esperando a hora seguinte às {hour.strftime('%H:%M:%S')}"
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                        print(message)
                        time.sleep(3600)
                    elif result == 0:
                        # Nesse caso foi criado o primeiro snapshot do Podio no BD. Próxima iteração nas próximas 12 horas.
                        now = datetime.datetime.now()
                        hours = now + datetime.timedelta(hours=9)
                        message = f"Esperando as próximas 12hs às {hours.strftime('%H:%M:%S')}"
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                        print(message)
                        time.sleep(43200)
                    else:
                        message = "Tentando novamente..."
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                        print(message)
                        time.sleep(1)
                elif res == 2:
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-2)
                    message = f"Esperando a hora seguinte às {hour.strftime('%H:%M:%S')}"
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                    time.sleep(3600)
                else:
                    hour = datetime.datetime.now() + datetime.timedelta(hours=-3)
                    message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado na criação/atualização do BD. Terminando o programa."
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_CHAT_ID']})
                    print(message)
                    exit(1)
                cycle += 1
