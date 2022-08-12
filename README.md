# podio_api_docker

Version of Podio Python Script inside docker container

Commands:

```shell
docker-compose up -d
```

```shell
docker pull "{dockerhub_username}"/podio_api:postgresql
```

```shell
docker build -t "{dockerhub_username}"/podio_api:postgresql .
```

```shell
docker push "{dockerhub_username}"/podio_api:postgresql
```

```shell
docker run --name podio_api -dit -e PODIO_CLIENT_ID="{podio_client_id}" -e PODIO_CLIENT_SECRET="{podio_client_secret}" -e PODIO_USERNAME="{podio_username}" -e PODIO_PASSWORD="{podio_password}" -e PODIO_APPS_IDS="{ids_comma_separated}" -e POSTGRES_HOST="{postgres_host}" -e POSTGRES_PORT="{postgres_port}" -e POSTGRES_USERNAME="{postgres_username}" -e POSTGRES_PASSWORD="{postgres_password}" -e POSTGRES_DATABASE="{postgres_database}" -e TELEGRAM_BOT_AUTH_TOKEN="{telegram_bot_auth_token}" -e TELEGRAM_BOT_CHAT_ID="{telegram_bot_chat_id}" "{dockerhub_username}"/podio_api:postgresql
```
