import datetime

from psycopg2 import Error as dbError
from get_mydb import getDB

from pypodio2.transport import TransportException
from podio_tools import handlingPodioError, getFieldValues

from telegram_tools import sendToBot
from logging_tools import logger, log_stream

# Inserindo ou atualizando dados no Banco. Retorna 0 se nao ocorreram erros
# Retorna 1 caso precise refazer a estrutura do Banco, excluindo alguma(s) tabela(s).
# Retorna 2 caso seja atingido o limite de requisições por hora
def insertItems(podio, apps_ids):
    mydb = getDB()
    cursor = mydb.cursor()
    for app_id in apps_ids:
        try:
            appInfo = podio.Application.find(app_id)
            spaceName = podio.Space.find(appInfo.get('space_id')).get('url_label').replace('-', '_')
            appName = appInfo.get('url_label').replace('-', '_')
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'podio' ORDER BY table_name;")
            tables = cursor.fetchall()
            tableName = spaceName+"__"+appName

            if (tableName,) in tables:
                tableLabels = []
                for field in appInfo.get('fields'):
                    if field['status'] == "active":
                        label = field['external_id']
                        label = label[:40]
                        tableLabels.append("\"" + label + "\"")

                # Fazendo requisicoes percorrendo todos os dados existentes
                # Para isso define-se o limite de cada consulta como 500 (o maximo) e o offset
                # Ou seja, a cada passo novo (offset) items são requisitados, com base na
                # quantidade de items obtidos na última iteração
                numberOfItems = podio.Application.get_items(appInfo.get('app_id'))['total']
                try:
                    for step in range(0, numberOfItems, 500):
                        # O valor padrão do offset é 0 de acordo com a documentação da API.
                        # Ordenando de forma crescente da data de criação para unificar a estruturação do BD.
                        filteredItems = podio.Item.filter(appInfo.get('app_id'),
                                        {"offset": step, "sort_by": "created_on", "sort_desc": False, "limit": 500})
                        items = filteredItems.get('items')
                        for item in items:
                            # Buscando a última atualização do Item no banco
                            cursor.execute(f"SELECT \"last_event_on\" FROM podio.{tableName} WHERE id='{item['item_id']}'")
                            last_event_on_podio = datetime.datetime.strptime(item['last_event_on'],
                                                    "%Y-%m-%d %H:%M:%S")
                            if cursor.rowcount > 0:
                                last_event_on_db = cursor.fetchone()[0]

                                if last_event_on_podio > last_event_on_db:
                                    message = f"Item com ID={item['item_id']} atualizado no Podio. Excluindo-o da tabela '{tableName}'"
                                    logger.info(message)
                                    sendToBot(log_stream.getvalue())
                                    cursor.execute(f"DELETE FROM podio.{tableName} WHERE id='{item['item_id']}'")

                            if cursor.rowcount == 0 or last_event_on_podio > last_event_on_db:
                                query = [f"INSERT INTO podio.{tableName}", " VALUES", "("]
                                query.extend([f"'{str(item['item_id'])}','{item['created_on']}','{last_event_on_podio}',"])
                                fields = [x for x in item['fields'] if f"\"{x['external_id'][:40]}\"" in tableLabels]
                                # Fazendo a comparação entre os campos existentes e os preenchidos
                                # Caso o campo esteja em branco no Podio, preencher com '?'
                                j = 0
                                for i in range(len(tableLabels)):
                                    if j < len(fields) and str("\"" + fields[j]['external_id'][:40] + "\"") == tableLabels[i]:
                                        values = getFieldValues(fields[j])
                                        j += 1
                                    else:
                                        values = "''"
                                    query.append(values)
                                    query.append(",")
                                query.pop()
                                query.append(")")
                                try:
                                    cursor.execute("".join(query))
                                    message = f"{''.join(query)}"
                                    logger.info(message)
                                    sendToBot(log_stream.getvalue())
                                    mydb.commit()
                                except dbError as err:
                                    message = f"Aplicativo alterado. Excluindo a tabela \"{tableName}\". {err}"
                                    logger.info(message)
                                    sendToBot(log_stream.getvalue())
                                    cursor.execute(f"DROP TABLE podio.{tableName}")
                                    return 1
                except TransportException as err:
                    handled = handlingPodioError(err)
                    if handled == 'status_504' or handled == 'null_query' or handled == 'status_400' or handled == 'token_expired':
                        return 1
                    if handled == 'rate_limit':
                        return 2

        except TransportException as err:
            handled = handlingPodioError(err)
            if handled == 'status_504' or handled == 'status_400' or handled == 'token_expired':
                return 1
            if handled == 'rate_limit':
                return 2
            return 1
    mydb.close()
    return 0
