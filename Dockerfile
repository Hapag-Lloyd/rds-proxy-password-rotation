# based on Amazon Linux 2023
FROM public.ecr.aws/lambda/python:3.13.2025.10.13.15

ARG LAMBDA_TASK_ROOT
WORKDIR ${LAMBDA_TASK_ROOT}

COPY . ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -e .

# run the function by default
CMD [ "src.rds_proxy_password_rotation.adapter.aws_lambda_function.lambda_handler" ]
