import os
# Usando a biblioteca de manipulação da API do Podio.
from pypodio2 import api

import mysql.connector
import time, datetime
import requests, json

# Timezone of GMT-03
TZ = datetime.timezone(datetime.timedelta(hours=-3))

def handling_podio_error(err):
    hour = datetime.datetime.now(TZ)
    message = ""
    try:
        if 'x-rate-limit-remaining' in err.status and err.status['x-rate-limit-remaining'] == '0':
            message = f"{hour.strftime('%H:%M:%S')} -> Quantidade de requisições chegou ao limite por hora."
            print(message)
            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            return "rate_limit"
        if err.status['status'] == '401':
            # Token expirado. Re-autenticando
            message = f"{hour.strftime('%H:%M:%S')} -> Token expirado. Renovando..."
            print(message)
            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            return "token_expired"
        if err.status['status'] == '400':
            if json.loads(err.content)['error_detail'] == 'oauth.client.invalid_secret':
                message = f"{hour.strftime('%H:%M:%S')} -> Secret inválido."
            elif json.loads(err.content)['error_detail'] == 'user.invalid.username':
                message = f"{hour.strftime('%H:%M:%S')} -> Usuário inválido."
            elif json.loads(err.content)['error_detail'] == 'oauth.client.invalid_id':
                message = f"{hour.strftime('%H:%M:%S')} -> ID do cliente inválido."
            elif json.loads(err.content)['error_detail'] == 'user.invalid.password':
                message = f"{hour.strftime('%H:%M:%S')} -> Senha do cliente inválido."
            else:
                message = f"{hour.strftime('%H:%M:%S')} -> Parâmetro nulo na query. {err}"
                print(message)
                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                return "null_query"
            return "status_400"
        if err.status['status'] == '504':
            message = f"{hour.strftime('%H:%M:%S')} -> Servidor demorou muito para responder. {err}"
            print(message)
            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            return "status_504"
        else:
            message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado no acesso a API. {err}"
        print(message)
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
    except requests.exceptions.ConnectionError as err:
        message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
        print(message)
    return "not_known_yet"

def get_all_workspaces(podio):
    # Obtendo informações de todas as organizações que o usuário tem acesso no Podio
    try:
        orgs = podio.Org.get_all()
        # Obtendo todas as workspaces que o usuário tem acesso
        hour = datetime.datetime.now(TZ)
        message = f"{hour.strftime('%H:%M:%S')} -> Sucesso na obtenção das orgs."
        print(message)
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
        return podio.Space.find_all_for_org(orgs[0]['org_id'])
    except api.transport.TransportException as err:
        return handling_podio_error(err)
    except requests.exceptions.ConnectionError as err:
        hour = datetime.datetime.now(TZ)
        message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
        print(message)

# Rotina para a criação inicial do banco de dados MySQL.
# Recebe a variável autenticada na API Podio e o cursor do BD.
def create_tables(podio, cursor):
    workspaces = get_all_workspaces(podio)
    if workspaces == 'token_expired' or workspaces == 'null_query':
        return 3
    if workspaces == 'rate_limit':
        return 2
    if type(workspaces) is list:
        # Verificando se as workspaces ja estão armazenadas no BD como databases. Se não, executar a criação
        for w in workspaces:
            space_name = w.get('url_label').replace("-", "_")
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
                        query = [f"CREATE TABLE IF NOT EXISTS {space_name}__{table_name}", "("]
                        query.append("`id` INTEGER PRIMARY KEY NOT NULL")
                        query.append(", `created_on` DATETIME")
                        #table_labels = []
                        for field in app_info.get('fields'):
                            if field['status'] == "active":
                                label = field['external_id']
                                # Alguns campos possuem nomes muito grandes
                                label = label[:40]
                                if "id" in label:
                                    label += str("".join(query).lower().count(f"`id")+1)
                                query.append(f", `{label}` TEXT")
                                #table_labels.append("`"+label+"`")
                        query.append(")")

                        #print(table_name)
                        cursor.execute("".join(query))
                        hour = datetime.datetime.now(TZ)
                        message = f"{hour.strftime('%H:%M:%S')} -> {''.join(query)}"
                        print(message)
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                    # Caso tabela esteja inativa no Podio, excluí-la
                    elif app.get('status') != "active" and (table_name,) in tables:
                        cursor.execute(f"DROP TABLE {space_name}__{table_name}")
                        hour = datetime.datetime.now(TZ)
                        message = f"{hour.strftime('%H:%M:%S')} -> Tabela inativa `{space_name}__{table_name}` excluída."
                        print(message)
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            except mysql.connector.Error as err:
                hour = datetime.datetime.now(TZ)
                message = f"{hour.strftime('%H:%M:%S')} -> Erro no acesso ao BD. {err}"
                print(message)
                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            except api.transport.TransportException as err:
                handled = handling_podio_error(err)
                if handled == 'token_expired':
                    return 3
                if handled == 'rate_limit':
                    return 2
                if handled == 'status_400' or handled == 'not_known_yet':
                    continue
            except requests.exceptions.ConnectionError as err:
                hour = datetime.datetime.now(TZ)
                message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                print(message)
        return 0
    #return 1
    # Não parando o fluxo
    return 3

# Inserindo dados no Banco. Retorna 0 se nao ocorreram erros
# Retorna 1 caso precise refazer a estrutura do Banco, excluindo alguma(s) tabela(s).
# Retorna 2 caso seja atingido o limite de requisições por hora
def insert_items(podio, cursor):
    workspaces = get_all_workspaces(podio)
    if workspaces == 'token_expired' or workspaces == 'null_query':
        return 1
    if type(workspaces) is list:
        for w in workspaces:
            space_name = w.get('url_label').replace("-", "_")
            try:
                apps = podio.Application.list_in_space(w.get('space_id'))
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()

                for app in apps:
                    table_name = app.get('url_label').replace('-', '_')
                    #print(table_name)
                    if (f"{space_name}__{table_name}",) in tables:
                        app_info = podio.Application.find(app.get('app_id'))
                        cursor.execute(f"SELECT COUNT(id) FROM {space_name}__{table_name}")
                        dbcount = cursor.fetchall()[0][0]

                        table_labels = []
                        for field in app_info.get('fields'):
                            if field['status'] == "active":
                                label = field['external_id']
                                label = label[:40]
                                table_labels.append("`" + label + "`")

                        # Fazendo requisicoes percorrendo todos os dados existentes
                        # Para isso define-se o limite de cada consulta como 500 (o maximo) e o offset
                        # Ou seja, a cada passo novo (offset) items são requisitados, com base na
                        # quantidade de items obtidos na última iteração
                        number_of_items = podio.Application.get_items(app_info.get('app_id'))['total']
                        if dbcount < number_of_items:
                            hour = datetime.datetime.now(TZ)
                            message = f"{hour.strftime('%H:%M:%S')} -> `{space_name}__{table_name}` tem {dbcount} itens no BD e {number_of_items} no Podio."
                            print(message)
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                            # Caso não seja possível inserir items em novas inspeções é necessário excluir a tabela
                            # recadastrando os dados no Banco
                            try:
                                for step in range(dbcount, number_of_items, 500):
                                    # O valor padrão do offset é 0 de acordo com a documentação da API.
                                    # Ordenando de forma crescente da data de criação para unificar a estruturação do BD.
                                    filtered_items = podio.Item.filter(app_info.get('app_id'), {"offset": step, "sort_by": "created_on", "sort_desc": False, "limit": 500})
                                    items = filtered_items.get('items')
                                    for item in items:
                                        query = ["INSERT INTO " + table_name, " VALUES", "("]
                                        query.extend([str(item['item_id']), ",", "\"" + str(item['created_on']) + "\"", ","])

                                        fields = [x for x in item['fields'] if f"`{x['external_id'][:40]}`" in table_labels]
                                        # Fazendo a comparação entre os campos existentes e os preenchidos
                                        # Caso o campo esteja em branco no Podio, preencher com '?'
                                        j = 0
                                        for i in range(len(table_labels)):
                                            s = "\""
                                            if j < len(fields) and str("`" + fields[j]['external_id'][:40] + "`") == table_labels[i]:
                                                # De acordo com o tipo do campo há uma determinada forma de recuperar esse dado
                                                if fields[j]['type'] == "contact":
                                                    # Nesse caso o campo é multivalorado, então concatena-se com um pipe '|'
                                                    # Podem haver aspas duplas inseridas no valor do campo. Substituir com aspas simples
                                                    for elem in fields[j]['values']:
                                                        s += elem['value']['name'].replace("\"", "'") + "|"
                                                    s = s[:-1]
                                                elif fields[j]['type'] == "category":
                                                    s += fields[j]['values'][0]['value']['text'].replace("\"", "'")
                                                elif fields[j]['type'] == "date" or fields[j]['type'] == "calculation" and 'start' in \
                                                        fields[j]['values'][0]:
                                                    s += fields[j]['values'][0]['start']
                                                elif fields[j]['type'] == "calculation" and 'value' in fields[j]['values'][0]:
                                                    s += fields[j]['values'][0]['value']
                                                elif fields[j]['type'] == "money":
                                                    s += fields[j]['values'][0]['currency'] + " " + fields[j]['values'][0]['value']
                                                elif fields[j]['type'] == "image":
                                                    s += fields[j]['values'][0]['value']['link']
                                                elif fields[j]['type'] == "embed":
                                                    s += fields[j]['values'][0]['embed']['url']
                                                elif fields[j]['type'] == "app":
                                                    # Nesse caso o campo é multivalorado, então concatena-se com um pipe '|'
                                                    for val in fields[j]['values']:
                                                        s += val['value']['title'].replace("\"", "'") + "|"
                                                    s = s[:-1]
                                                else:
                                                    value = str(fields[j]['values'][0]['value'])
                                                    s += value.replace("\"", "'")
                                                s += "\""
                                                j += 1
                                            else:
                                                s += "?\""
                                            query.append(s)
                                            query.append(",")
                                        query.pop()
                                        query.append(")")
                                        try:
                                            cursor.execute("".join(query))
                                            hour = datetime.datetime.now(TZ)
                                            message = f"{hour.strftime('%H:%M:%S')} -> {''.join(query)}"
                                            print(message)
                                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                                            mydb.commit()
                                        except mysql.connector.Error as err:
                                            hour = datetime.datetime.now(TZ)
                                            message = f"{hour.strftime('%H:%M:%S')} -> Aplicativo alterado. Excluindo a tabela `{space_name}__{table_name}`."
                                            print(message)
                                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                                            cursor.execute(f"DROP TABLE {space_name}__{table_name}")
                                            return 1
                            except api.transport.TransportException as err:
                                handled = handling_podio_error(err)
                                if handled == 'status_504' or handled == 'null_query' or handled == 'status_400' or handled == 'token_expired':
                                    return 1
                                if handled == 'rate_limit':
                                    return 2
                        elif dbcount > number_of_items:
                            hour = datetime.datetime.now(TZ)
                            message = f"{hour.strftime('%H:%M:%S')} -> Itens excluídos do Podio. Excluindo a tabela `{space_name}__{table_name}` e recriando-a no próximo ciclo."
                            print(message)
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                            cursor.execute(f"DROP TABLE {space_name}__{table_name}")
                            #return 1
                            continue

            except api.transport.TransportException as err:
                hour = datetime.datetime.now(TZ)
                handled = handling_podio_error(err)
                if handled == 'status_504' or handled == 'status_400' or handled == 'token_expired':
                    return 1
                if handled == 'rate_limit':
                    return 2
                return 1
            except requests.exceptions.ConnectionError as err:
                hour = datetime.datetime.now(TZ)
                message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                print(message)
        return 0
    return 1

def convert(seconds):
    hours = seconds // 3600
    seconds %= 3600
    mins = seconds // 60
    seconds %= 60
    return hours, mins, seconds

def timer(seconds):
    print('=== Temporizador ===')
    count = 0
    while count < seconds:
        hours, mins, secs = convert(count)
        timer = '{:02d}:{:02d}:{:02d}'.format(hours, mins, secs)
        print(timer, end='\r')
        time.sleep(1)
        count += 1

if __name__ == '__main__':
    # Recuperando as variáveis de ambiente e guardando
    client_id = os.environ['PODIO_CLIENT_ID']
    client_secret = os.environ['PODIO_CLIENT_SECRET']
    username = os.environ['PODIO_USERNAME']
    password = os.environ['PODIO_PASSWORD']

    #print(client_id, client_secret, username, password)
    message = "==== PODIO API PYTHON SCRIPT (MySQL) ===="
    print(message)
    try:
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
    except requests.exceptions.ConnectionError as err:
        hour = datetime.datetime.now(TZ)
        message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
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
        hour = datetime.datetime.now(TZ)
        handled = handling_podio_error(err)
        message = f"{hour.strftime('%H:%M:%S')} -> Terminando o programa."
        print(message)
        if handled == 'status_400':
            try:
                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            except requests.exceptions.ConnectionError as err:
                message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                print(message)
        exit(1)
    else:
        #print(podio)
        #print(workspaces)
        try:
            # Acessando o BD para armazenar os dados das workspaces nele
            mydb = mysql.connector.connect(
                host=os.environ['MYSQL_HOST'],
                port=os.environ['MYSQL_PORT'],
                user=os.environ['MYSQL_USERNAME'],
                password=os.environ['MYSQL_PASSWORD'],
                database=os.environ['MYSQL_DATABASE']
            )
            # print(mydb)
            cursor = mydb.cursor()
        except mysql.connector.Error as err:
            hour = datetime.datetime.now(TZ)
            message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado no acesso inicial ao BD. Terminando o programa. {err}"
            print(message)
            try:
                requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
            except requests.exceptions.ConnectionError as err:
                message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                print(message)
            exit(1)
        else:
            cycle = 1
            while True:
                message = f"==== Ciclo {cycle} ===="
                print(message)
                try:
                    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                except requests.exceptions.ConnectionError as err:
                    hour = datetime.datetime.now(TZ)
                    message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                    print(message)
                res = create_tables(podio, cursor)
                if res == 0:
                    result = insert_items(podio, cursor)
                    # Caso o limite de requisições seja atingido, espera-se mais 1 hora até a seguinte iteração
                    if result == 2:
                        hour = datetime.datetime.now(TZ) + datetime.timedelta(hours=1)
                        message = f"Esperando a hora seguinte. Até às {hour.strftime('%H:%M:%S')}"
                        print(message)
                        try:
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                        except requests.exceptions.ConnectionError as err:
                            hour = datetime.datetime.now(TZ)
                            message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                            print(message)
                        timer(3600)
                        podio = api.OAuthClient(
                            client_id,
                            client_secret,
                            username,
                            password
                        )
                        mydb.close()
                        mydb = mysql.connector.connect(
                            host=os.environ['MYSQL_HOST'],
                            port=os.environ['MYSQL_PORT'],
                            user=os.environ['MYSQL_USERNAME'],
                            password=os.environ['MYSQL_PASSWORD'],
                            database=os.environ['MYSQL_DATABASE']
                        )
                        cursor = mydb.cursor()
                    elif result == 0:
                        # Nesse caso foi criado o primeiro snapshot do Podio no BD. Próxima iteração nas próximas 12 horas.
                        now = datetime.datetime.now(TZ)
                        hours = now + datetime.timedelta(hours=8)
                        message = f"Esperando as próximas 8hs. Até às {hours.strftime('%H:%M:%S')}"
                        print(message)
                        try:
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                        except requests.exceptions.ConnectionError as err:
                            hour = datetime.datetime.now(TZ)
                            message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                            print(message)
                        timer(28800)   
                        podio = api.OAuthClient(
                            client_id,
                            client_secret,
                            username,
                            password
                        )   
                        mydb.close()
                        mydb = mysql.connector.connect(
                            host=os.environ['MYSQL_HOST'],
                            port=os.environ['MYSQL_PORT'],
                            user=os.environ['MYSQL_USERNAME'],
                            password=os.environ['MYSQL_PASSWORD'],
                            database=os.environ['MYSQL_DATABASE']
                        )
                        cursor = mydb.cursor()
                    else:
                        message = "Tentando novamente..."
                        print(message)
                        podio = api.OAuthClient(
                            client_id,
                            client_secret,
                            username,
                            password
                        )
                        try:
                            requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                        except requests.exceptions.ConnectionError as err:
                            hour = datetime.datetime.now(TZ)
                            message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                            print(message)
                        time.sleep(1)
                elif res == 2:
                    hour = datetime.datetime.now(TZ) + datetime.timedelta(hours=1)
                    message = f"Esperando a hora seguinte. Até às {hour.strftime('%H:%M:%S')}"
                    print(message)
                    try:
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                    except requests.exceptions.ConnectionError as err:
                        message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                        print(message)
                    timer(3600)
                    podio = api.OAuthClient(
                        client_id,
                        client_secret,
                        username,
                        password
                    )
                    mydb.close()
                    mydb = mysql.connector.connect(
                        host=os.environ['MYSQL_HOST'],
                        port=os.environ['MYSQL_PORT'],
                        user=os.environ['MYSQL_USERNAME'],
                        password=os.environ['MYSQL_PASSWORD'],
                        database=os.environ['MYSQL_DATABASE']
                    )
                    cursor = mydb.cursor()
                elif res == 3:
                    message = "Tentando novamente..."
                    print(message)
                    podio = api.OAuthClient(
                        client_id,
                        client_secret,
                        username,
                        password
                    )
                    try:
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                    except requests.exceptions.ConnectionError as err:
                        hour = datetime.datetime.now(TZ)
                        message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                        print(message)
                    time.sleep(1)
                else:
                    hour = datetime.datetime.now(TZ)
                    message = f"{hour.strftime('%H:%M:%S')} -> Erro inesperado na criação/atualização do BD. Terminando o programa."
                    print(message)
                    try:
                        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_AUTH_TOKEN']}/sendMessage", data={'text': message, 'chat_id': os.environ['TELEGRAM_BOT_CHAT_ID']})
                    except requests.exceptions.ConnectionError as err:
                        message = f"{hour.strftime('%H:%M:%S')} -> Erro no post para o Telegram. {err}"
                        print(message)
                    exit(1)
                cycle += 1
