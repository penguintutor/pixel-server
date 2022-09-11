FROM python:alpine

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/pixel-server/

RUN apk add libffi-dev build-base linux-headers --no-cache && \
    pip install --upgrade --no-cache-dir rpi_ws281x RPi.GPIO setuptools argon2_cffi Flask-WTF && \
    touch users.cfg auth.cfg

COPY . .

RUN cp defaults.cfg pixelserver.cfg

ENTRYPOINT [ "/bin/sh", "-c", "python pixelserver.py & crond -f" ]

#docker run -d -v auth_cfg:/opt/pixel-server/auth.cfg -v pixel_cfg:/opt/pixel-server/pixelserver.cfg -v user_cfg:/opt/pixel-server/users.cfg -v crontab:/etc/crontabs/root --device=/dev/vcio --cap-add=SYS_RAWIO --device=/dev/mem --security-opt=systempaths=unconfined --security-opt=apparmor=unconfined --device=/dev/spidev0.0 --device=/dev/i2c-1 --device=/dev/gpiomem --restart unless-stopped -p 85:80 --name pixel-server pixel-server
# Edit crontab in container only persistently: docker exec -it pixel-server crontab -e
# The file location is different, so users would need to add it into crontab as:
# */5 * * * * wget -O customlight.cfg http://api.thingspeak.com/channels/1417/field/2/last.txt
# Add user persistently: docker exec -it pixel-server python3 createadmin.py <username> <password> >> users.cfg
