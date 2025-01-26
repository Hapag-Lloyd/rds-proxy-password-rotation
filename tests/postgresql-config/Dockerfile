FROM postgres:13-alpine

RUN apk add --no-cache openssl

RUN mkdir /certs

WORKDIR /certs

RUN openssl req -new -x509 -days 3650 -nodes -text -out server.crt -keyout server.key -subj "/CN=localhost" && \
    chmod og-rwx server.key && \
    openssl req -new -nodes -text -out root.csr -keyout root.key -subj "/CN=localhost" && \
    chmod og-rwx root.key && \
    openssl x509 -req -in root.csr -text -days 3650 -extfile /etc/ssl/openssl.cnf -extensions v3_ca -signkey root.key -out root.crt && \
    chown 0:70 /certs/* && \
    chmod 640 /certs/*
