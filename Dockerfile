FROM python:alpine

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apk add build-base linux-headers libffi-dev --no-cache && \
    pip install --upgrade --no-cache-dir pip argon2_cffi Flask-WTF rpi_ws281x flask adafruit-blinka RPi.GPIO adafruit-python-shell setuptools adafruit-circuitpython-neopixel && \
    echo "*/5 * * * * wget -O /opt/pixel-server/customlight.cfg http://api.thingspeak.com/channels/1417/field/2/last.txt" >> /etc/crontabs/root
    
WORKDIR /opt/pixel-server/

COPY . .

ENTRYPOINT [ "/bin/sh", "-c", "python pixelserver.py & crond -f" ]
