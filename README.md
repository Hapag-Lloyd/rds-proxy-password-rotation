# rds-proxy-password-rotation

:warning: **Work in progress** :warning:

- implement step CREATE_SECRET
- implement step SET_SECRET
- implement step TEST_SECRET
- implement step FINISH_SECRET
- add Terraform module

Python script for multi-user password rotation using RDS and RDS proxy. It supports a separate credential for the application.

## Pre-requisites

1. Python 3.10 or later
2. For each db user:
   1. Create a secret in AWS Secrets Manager with the following key-value pairs:
      - `username`: The username for the user
      - `password`: The password for the user
      This credential will be used by the application to connect to the proxy. You may add additional key-value pairs as needed.
   2. Clone the user in the database and grant the necessary permissions. We suggest to add a `-clone` suffix to the username.
   3. Create two secrets (for the original user and the clone) in AWS Secrets Manager with the following key-value pairs:
     - `username`: The username for the user
     - `password`: The password for the user
   These credentials are used by the proxy to connect to the database. You may add additional key-value pairs as needed.

## Architecture

![Architecture](assets/architecture.png)

## Challenges with RDS and RDS Proxy

RDS Proxy is a fully managed, highly available database proxy for Amazon Relational Database Service (RDS) that makes applications
more scalable, more resilient to database failures, and more secure. It allows applications to pool and share database connections
to improve efficiency and reduce the load on your database instances.

However, RDS Proxy does not support multi-user password rotation out of the box. This script provides a solution to this problem.

Using an RDS Proxy requires a secret in AWS Secrets Manager with the credentials to connect to the database. This secret is used by
the proxy to connect to the database. The proxy allows the application to connect to the database using the same credentials and
then forwards the requests to the database with the same credentials. This means that the credentials in the secret must be valid
in the database at all times. But what if you want to rotate the password for the user that the proxy uses to connect to the
database? You can’t just update the secret in SecretsManager because the proxy will stop working as soon as the secret is updated.
And you can’t just update the password in the database because the proxy will stop working as soon as the password is updated.

## Why password rotation is a good practice

Password rotation is a good idea for several reasons:

1. **Enhanced Security**: Regularly changing passwords reduces the risk of unauthorized access due to compromised credentials.
2. **Mitigates Risk**: Limits the time window an attacker has to exploit a stolen password.
3. **Compliance**: Many regulatory standards and security policies require periodic password changes.
4. **Reduces Impact of Breaches**: If a password is compromised, rotating it ensures that the compromised password is no longer valid.
5. **Encourages Good Practices**: Promotes the use of strong, unique passwords and discourages password reuse.
