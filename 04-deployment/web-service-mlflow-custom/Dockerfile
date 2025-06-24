FROM python:3.12-slim

# --no-cache-dir prevents pip from storing downloaded packages in cache
# This reduces Docker image size by not keeping unnecessary cached files
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir uvicorn

WORKDIR /app

COPY [ "requirements.txt", "./" ]

RUN pip install --no-cache-dir -r requirements.txt

# Copy the predict.py file first for model download
COPY [ "predict.py", "./" ]

EXPOSE 9696

ENTRYPOINT [ "uvicorn", "--host=0.0.0.0", "--port=9696", "predict:app" ]