# Use a modern, maintained Python base image
FROM python:3.10.4-slim-bullseye

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Update system and install dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        wget \
        ffmpeg \
        build-essential \
        libffi-dev \
        libssl-dev \
        python3-dev \
        ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Expose port if needed (optional)
# EXPOSE 8080

# Default command to run your bot
CMD ["python", "main.py"]
