FROM python:3.11-slim as python-base

ENV DOCKER=true
ENV GIT_PYTHON_REFRESH=quiet
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install libcairo2 git build-essential -y --no-install-recommends

RUN apt install ffmpeg libavcodec-dev libavutil-dev libavformat-dev libswscale-dev libavdevice-dev neofetch -y

RUN rm -rf /var/lib/apt/lists /var/cache/apt/archives /tmp/*

RUN mkdir /data

COPY . /data
WORKDIR /data

RUN python -m venv .venv

RUN .venv/bin/pip install --no-warn-script-location --no-cache-dir -U -r requirements.txt

EXPOSE 8080

CMD . .venv/bin/activate && python -m hikka
