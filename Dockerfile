# Use maintained Python base (Bookworm instead of Buster)
FROM python:3.10-slim-bookworm

# Prevent apt warnings about tzdata
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        wget \
        python3-pip \
        bash \
        neofetch \
        ffmpeg \
        software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Upgrade pip + install Python deps
RUN pip install --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Expose app port
EXPOSE 8000

# Run flask + your custom Python module
CMD flask run -h 0.0.0.0 -p 8000 & python3 -m devgagan
