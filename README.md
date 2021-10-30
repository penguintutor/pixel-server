# pixel-server
Wireless control of PixelStrips or NeoPixels using a web graphical interface running on a Raspberry Pi.

Works with any Raspberry Pi. 

For more details see:
<http://www.penguintutor.com/projects/pixel-server>

![NeoPixel web application](http://www.penguintutor.com/projects/images/pixelserver-webapplication.png)

## Colors

The color of the pixels depends upon your actual strip. In the default code then grey is set to a very low value to show a noticeable difference on my pixel strip. This may appear to be near to black on the screen, but shows fairly bright on the strip. The same problem occurs with lighter colors such as light green which may appear almost white on the pixel strip.

## Sequences

The sequences are defined in pixelseq.py. You can add your own for any additional sequences you would like. You will need to create the appropriate method and update SeqList.pixel_sequences and PixelSeq.seq_methods.

It's also possible to create other sequences using the built-in sequences with specific color sequences. In particular you can add black for any pixels that you would like tried turned off.

For example try a chaser with:
Black; Black; White; White
Grey; White; White; White; Grey; Black

## Install

This is designed to run on a Raspberry Pi with PixelStrip / NeoPixels / WS2812B LEDs connected to a gpio pin. It is recommended that you use a voltage level-shifter.
For more details see:
<http://www.penguintutor.com/projects/pixelstrip>


To install the pre-requisite library first install the RPI ws281x library:

    sudo pip3 install rpi_ws281x

It is recommended to install directly from git, which will allow for install of future updates. Note that updates will replace any custom sequences you have created.

On a Raspberry Pi, open a terminal and enter the following commands:

    git clone https://github.com/penguintutor/pixel-server.git 

Then to have it start automatically run the following:

    sudo cp /home/pi/pixel-server/pixelserver.service /etc/systemd/system/
    sudo chown root:root /etc/systemd/system/pixelserver.service
    sudo chmod 644 /etc/systemd/system/pixelserver.service

Enable using:

    sudo systemctl start pixelserver.service
    sudo systemctl enable pixelserver.service

For more information see: <http://www.penguintutor.com/raspberrypi/startup>

# Automation

You can automate the light sequences being turned on and off by using crontab. For example:

    0 22 * * * wget -O /dev/null http://127.0.0.1/set?seq=alloff&delay=976&reverse=0&colors=ffffff
    0 16 * * 1-5 wget -O /dev/null http://127.0.0.1/set?seq=chaser&delay=5000&reverse=1&colors=ffffff,ffffff,ffffff,0000ff,ffffff,ffffff,ffffff,00ffff

