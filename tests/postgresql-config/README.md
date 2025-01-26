# Generate a self-signed certificate for PostgreSQL

```bash
openssl genrsa -out server.key 2048
chmod 400 server.key

openssl req -new -key server.key -days 365 -out server.crt -x509 -subj "/CN=localhost"
cp server.crt root.crt


openssl req -new -text -passout pass:abcd -subj "/CN=localhost" -out server.req
openssl rsa -in privkey.pem -passin pass:abcd -out server.key
openssl req -x509 -in server.req -text -key server.key -out server.crt

chown 0600 server.key
```

