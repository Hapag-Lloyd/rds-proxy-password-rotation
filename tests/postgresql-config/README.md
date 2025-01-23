# Generate a self-signed certificate for PostgreSQL

```bash
# use localhost as the common name
openssl req -new -text -passout pass:abcd -out server.req
openssl rsa -in privkey.pem -passin pass:abcd -out server.key
openssl req -x509 -in server.req -text -key server.key -out server.crt

chown 0600 server.key
```

