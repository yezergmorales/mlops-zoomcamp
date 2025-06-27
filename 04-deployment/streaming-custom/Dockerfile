FROM public.ecr.aws/lambda/python:3.12
RUN pip install -U pip
RUN pip install pipenv 

# WORKDIR /app --> in this case we don't need due to there is a especific
# directory inside the image.

COPY [ "requirements.txt", "./" ]

RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir -r requirements.txt

COPY [ "lambda_function.py", "./" ]

CMD [ "lambda_function.lambda_handler" ]
