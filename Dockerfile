FROM python:alpine

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apk add build-base linux-headers --no-cache && \
    pip install --upgrade --no-cache-dir rpi_ws281x flask RPi.GPIO setuptools

COPY . .

CMD [ "python", "pixelserver.py" ]
