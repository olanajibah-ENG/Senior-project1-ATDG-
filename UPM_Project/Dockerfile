    FROM python:3.10-slim

    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1

    WORKDIR /app

    RUN apt-get update \
        && apt-get install -y --no-install-recommends \
            gcc \
            default-libmysqlclient-dev \
            pkg-config \
            bash \
            libssl-dev \
            libffi-dev \
            curl \
        && rm -rf /var/lib/apt/lists/*

    COPY requirements.txt /app/
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . /app/

    RUN chmod +x /app/entrypoint.sh && \
        sed -i 's/\r$//' /app/entrypoint.sh 2>/dev/null || true

    EXPOSE 8000
    ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]