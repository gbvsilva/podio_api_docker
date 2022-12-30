FROM python:3.8-alpine

# Creating folder
RUN mkdir /opt/podio_api
COPY . /opt/podio_api
WORKDIR /opt/podio_api

# Installing dependencies
RUN apk update
RUN apk add --no-cache py3-pip python3-dev git gcc

# Getting pypodio2 library
RUN git clone https://github.com/podio/podio-py.git
RUN cd podio-py && python setup.py install

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Cleaning cache
RUN apk del git && rm -rf /var/cache/apk/*

# Setting entrypoint
CMD ["-u", "/opt/podio_api/podio_api.py"]
ENTRYPOINT [ "python3" ]
