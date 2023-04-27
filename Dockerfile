FROM python:3.8-alpine

# Creating folder
RUN mkdir /opt/podio_api
COPY . /opt/podio_api
WORKDIR /opt/podio_api

# Installing dependencies
RUN apk update
RUN apk add --no-cache tzdata py3-pip python3-dev git

# Set the timezone
ENV TZ=America/Fortaleza
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# To install requirements.txt
RUN pip install --no-cache-dir wheel

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Cleaning cache
RUN apk del git && rm -rf /var/cache/apk/*

# Setting entrypoint
CMD ["-u", "/opt/podio_api/podio_api.py"]
ENTRYPOINT [ "python3" ]
