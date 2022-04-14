FROM python:latest

RUN pip install --upgrade rpi_ws281x flask

COPY . .

CMD [ "python" ,"pixelserver.py" ]
