FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY src/requirements.txt .

RUN pip3 install -r requirements.txt --target .

COPY src/. .

CMD [ "lambda_function.lambda_handler" ]