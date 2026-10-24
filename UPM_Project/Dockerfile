FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Use faster apt settings
RUN echo "Acquire::http::Timeout \"10\";" > /etc/apt/apt.conf.d/99timeout && \
    echo "Acquire::Retries \"5\";" >> /etc/apt/apt.conf.d/99timeout

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends -qq \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        bash \
        libssl-dev \
        libffi-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chmod +x /app/entrypoint.sh && \
        sed -i 's/\r$//' /app/entrypoint.sh 2>/dev/null || true

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]