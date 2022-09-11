FROM python:alpine

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/pixel-server/

RUN apk add libffi-dev build-base linux-headers --no-cache && \
    pip install --upgrade --no-cache-dir rpi_ws281x RPi.GPIO setuptools argon2_cffi Flask-WTF

COPY . .

ENTRYPOINT [ "/bin/sh", "-c", "python pixelserver.py & crond -f" ]
