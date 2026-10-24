# ⭐ Option B: Multi-stage optimized Dockerfile for Debian-slim
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Improve apt reliability and keep image small
RUN echo "Acquire::http::Timeout \"10\";" > /etc/apt/apt.conf.d/99timeout && \
    echo "Acquire::Retries \"5\";" >> /etc/apt/apt.conf.d/99timeout && \
    apt-get update -qq && \
    apt-get install -y --no-install-recommends -qq \
        gcc \
        default-libmysqlclient-dev \
        pkg-config && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
COPY requirements.txt .
# Build wheels in builder stage to avoid compiling in final image
# Remove `--no-deps` so pip builds wheels for dependencies (e.g. asgiref)
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- final stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Provide runtime client library required by mysqlclient (mariadb/mysql client)
RUN echo "Acquire::http::Timeout \"10\";" > /etc/apt/apt.conf.d/99timeout && \
    echo "Acquire::Retries \"3\";" >> /etc/apt/apt.conf.d/99timeout && \
    apt-get update -qq && \
    apt-get install -y --no-install-recommends -qq \
        libmariadb3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
# Copy prebuilt wheels and install from them (no compilation on final image)
COPY --from=builder /wheels /wheels
RUN pip install --no-index --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application source
COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]