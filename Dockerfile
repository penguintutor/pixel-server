FROM python:alpine

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apk add libffi-dev build-base linux-headers --no-cache && \
    pip install --upgrade --no-cache-dir rpi_ws281x flask RPi.GPIO setuptools argon2_cffi Flask-WTF && \
    echo "*/5 * * * * wget -O /opt/pixel-server/customlight.cfg http://api.thingspeak.com/channels/1417/field/2/last.txt" >> /etc/crontabs/root

WORKDIR /opt/pixel-server/

COPY . .

ENTRYPOINT [ "/bin/sh", "-c", "python pixelserver.py & crond -f" ]

#docker run -d --device=/dev/vcio --cap-add=SYS_RAWIO --device=/dev/mem --security-opt=systempaths=unconfined --security-opt=apparmor=unconfined --device=/dev/spidev0.0 --device=/dev/i2c-1 --device=/dev/gpiomem --restart unless-stopped -p 85:80 --name pixel-server pixel-server
#https://github.com/penguintutor/pixel-server/pull/3/files
