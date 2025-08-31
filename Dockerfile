# Use a maintained Python image
FROM python:3.10.4-slim-bullseye

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        wget \
        ffmpeg \
        bash \
        neofetch \
        software-properties-common \
        build-essential \
        libffi-dev \
        libssl-dev \
        python3-dev \
        ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port for Flask
EXPOSE 8000

# Run Flask and your bot
CMD ["bash", "-c", "flask run --host=0.0.0.0 --port=8000 & python3 -m devgagan"]
