FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update && \
apt-get install -y wget unzip && \
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
apt install -y ./google-chrome-stable_current_amd64.deb && \
rm google-chrome-stable_current_amd64.deb && \
apt-get clean

RUN apt-get update && apt-get install -y \
    xvfb \
    xdotool \
    imagemagick \
    lsof \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 celeryuser

COPY . /app

RUN chmod +x /app/entrypoint.sh

USER celeryuser
ENTRYPOINT ["/app/entrypoint.sh"]

