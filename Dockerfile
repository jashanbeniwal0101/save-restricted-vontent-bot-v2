# Use Python 3.10 on Debian Bookworm
FROM python:3.10.4-bookworm

# Set working directory
WORKDIR /app

# Update and install dependencies
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y git curl wget bash neofetch ffmpeg software-properties-common python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port for Flask
EXPOSE 8000

# Run both Flask and your bot
CMD bash -c "flask run -h 0.0.0.0 -p 8000 & python3 -m devgagan"
