# podio_api_docker

Version of Podio Python Script inside docker container

Commands:

```shell
docker-compose up -d
```

```shell
docker pull "{dockerhub_username}"/podio_api:mysql
```

```shell
docker build -t "{dockerhub_username}"/podio_api:mysql .
```

```shell
docker push "{dockerhub_username}"/podio_api:mysql
```

```shell
docker run --name podio_api --network host -dit -e PODIO_CLIENT_ID="{podio_client_id}" -e PODIO_CLIENT_SECRET="{podio_client_secret}" -e PODIO_USERNAME="{podio_username}" -e PODIO_PASSWORD="{podio_password}" -e PODIO_APPS_IDS="{ids_comma_separated}" -e MYSQL_HOST="{mysql_host}" -e MYSQL_PORT="{mysql_port}" -e MYSQL_USERNAME="{mysql_username}" -e MYSQL_PASSWORD="{mysql_password}" -e MYSQL_DATABASE="{mysql_database}" -e TELEGRAM_BOT_AUTH_TOKEN="{telegram_bot_auth_token}" -e TELEGRAM_BOT_CHAT_ID="{telegram_bot_chat_id}" "{dockerhub_username}"/podio_api:mysql
```
