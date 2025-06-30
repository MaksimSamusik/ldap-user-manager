FROM python:3.12

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

ENV IN_DOCKER_CONTAINER=True

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY . .