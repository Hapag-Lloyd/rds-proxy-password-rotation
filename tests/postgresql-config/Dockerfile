FROM postgres:16.6-alpine

COPY ssl/server.key /var/lib/postgresql/server.key
COPY ssl/server.crt /var/lib/postgresql/server.crt

# update the privileges on the .key, no need to touch the .crt
RUN chmod 0600 /var/lib/postgresql/server.key && \
    chown postgres:postgres /var/lib/postgresql/server.key
