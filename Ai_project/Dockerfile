FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Use faster apt mirror and timeout settings
RUN echo "Acquire::http::Timeout \"10\";" > /etc/apt/apt.conf.d/99timeout && \
    echo "Acquire::Retries \"5\";" >> /etc/apt/apt.conf.d/99timeout && \
    echo "Acquire::http::Pipeline-Depth \"0\";" >> /etc/apt/apt.conf.d/99timeout

# Install system dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends -qq \
        fonts-liberation \
        libpangocairo-1.0-0 \
        libcairo2-dev \
        gcc \
        g++ \
        pkg-config \
        bash \
        libssl-dev \
        libffi-dev \
        python3-dev \
        libtree-sitter-dev \
        libpango-1.0-0 \
        libharfbuzz0b \
        libpangoft2-1.0-0 \
        libjpeg-dev \
        libopenjp2-7-dev \
        libtiff-dev \
        unrar-free \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt /app/

# Install all requirements (pydantic v2 + langchain are compatible)
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Full requirements failed, installing minimal set..." && \
     pip install --no-cache-dir \
       Django==4.2.14 djangorestframework pymongo "celery[redis]" \
       djangorestframework-simplejwt django-cors-headers==4.9.0 drf-yasg \
       django-celery-results django-celery-beat django-environ \
       gunicorn whitenoise requests python-dotenv \
       reportlab Pillow html5lib xhtml2pdf \
       "pydantic>=2.0.0,<3.0.0" typing-extensions \
       "langchain>=0.1.0" "langchain-core>=0.1.0" "langgraph>=0.1.0")

# Verify tree-sitter
RUN python -c "import tree_sitter; import tree_sitter_languages; print('Tree-sitter OK')" || \
    (echo "Tree-sitter failed, installing fallback..." && \
     pip install --no-cache-dir tree-sitter==0.20.4 tree-sitter-languages==1.6.1)

COPY . /app/

RUN chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh 2>/dev/null || true

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
