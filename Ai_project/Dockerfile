FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies in stages with better error handling
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fonts-liberation \
        libpangocairo-1.0-0 \
        libcairo2-dev \
        gcc \
        g++ \
        pkg-config \
        bash \
        libssl-dev \
        libffi-dev \
        curl \
        git \
        make \
        cmake \
        build-essential \
        python3-dev \
        libtree-sitter-dev \
        libpango-1.0-0 \
        libharfbuzz0b \
        libpangoft2-1.0-0 \
        libjpeg-dev \
        libopenjp2-7-dev \
        libtiff-dev \
        unrar \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel first
RUN pip install --upgrade pip setuptools wheel

# Copy and install requirements with error handling
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Failed to install full requirements, trying minimal version..." && \
     pip install --no-cache-dir Django==4.2.14 djangorestframework pymongo djangorestframework-simplejwt django-cors-headers drf-yasg django-environ gunicorn requests python-dotenv reportlab Pillow)

# Tree-sitter verification with fallback
RUN python -c "import tree_sitter; import tree_sitter_languages; print('Tree-sitter OK')" || \
    (echo "Tree-sitter failed, installing fallback..." && \
     pip install --no-cache-dir tree-sitter==0.20.4 tree-sitter-languages==1.6.1)

COPY . /app/

RUN chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh 2>/dev/null || true

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
