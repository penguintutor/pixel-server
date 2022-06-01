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


To install the RPI ws281x library:

    sudo pip3 install rpi_ws281x

It is recommended to install this program directly from git, which will allow for install of future updates. Note that updates will replace any custom sequences you have created. To provide support for different usernames I recommend installing into the /opt directory.

On a Raspberry Pi, open a terminal and enter the following commands:

    cd /opt
    sudo mkdir pixel-server
    sudo chown $USER: pixel-server 
    git clone https://github.com/penguintutor/pixel-server.git pixel-server

Then to have it start automatically run the following:

    sudo cp /opt/pixel-server/pixelserver.service /etc/systemd/system/
    sudo chown root:root /etc/systemd/system/pixelserver.service
    sudo chmod 644 /etc/systemd/system/pixelserver.service

Enable using:

    sudo systemctl start pixelserver.service
    sudo systemctl enable pixelserver.service

There is also a video providing a step-by-step guide to installing this on a Raspberry Pi. [Installing Pixel Server on Raspberry Pi OS 64-bit](https://youtu.be/D1VsBHWuY_I)

For more information see: [Penguin Tutor guide to starting programs automatically on a Raspberry Pi](http://www.penguintutor.com/raspberrypi/startup)


# Security

## Enable SSL (HTTPS)

This explains how you can use the Flask (development) server with https using Nginx as a reverse proxy. This uses a free security certificate from [Let's Encrypt](https://letsencrypt.org/). This means that I am able to setup Nginx as a reverse proxy on my home server, which could be used to provide encrypted connections to different services. 


### On local pi with pixel-server
Setup Flask to use gunicorn

sudo apt update
sudo apt ugprade

sudo apt install python3-gunicorn

Create a file /etc/systemd/system/gunicorn.service with the following:
    [Unit]
    Description=gunicorn daemon
    After=network.target
    
    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/var/www/application/
    
    ExecStart=/usr/bin/gunicorn --access-logfile - --workers 3 --bind
    unix:/var/www/application.sock wsgi:app
    
    [Install]
    WantedBy=multi-user.target

    

    

### On Nginx reverse proxy

This does not have to be on the same server as pixel-server.

First make sure your system is up-to-date

sudo apt update
sudo apt upgrade

sudo apt install certbot
sudo apt install python3-certbot-nginx 
sudo apt install nginx

add new file in sites-available

ln -s to /etc/nginx/sites-enabled


    location /demo/ {
        proxy_pass http://<localaddress>/;
    }


sudo certbot --nginx -d home.penguintutor.com

This updates /etc/nginx/sites-enabled

update with 
sudo nginx -t
sudo nginx -s reload

Add the following to crontab for root:
0 12 * * * /usr/bin/certbot renew --quiet

This checks for updates on a daily basis and if required renew

## Login

New login features requires that users login to the web interface. This would prevent automation from working, therefore an alternative is allowed where clients can be pre-authorized based on their IP address. 

If automation runs on the local machine then it is recommended that only the loopback IP address 127.0.0.1 is pre-authorized, but additional IP addresses can be enabled for use by WiFi switches, such as those used in the [ESP32 wireless capacitive touch switch](http://www.penguintutor.com/projects/esp32-captouch).


# Automation

You can automate the light sequences being turned on and off by using crontab. For example:

    0 22 * * * wget -O /dev/null http://127.0.0.1/set?seq=alloff&delay=976&reverse=0&colors=ffffff
    0 16 * * 1-5 wget -O /dev/null http://127.0.0.1/set?seq=chaser&delay=5000&reverse=1&colors=ffffff,ffffff,ffffff,0000ff,ffffff,ffffff,ffffff,00ffff

## Toggle

An additional setting available for automation is &toggle=True. When turned on then the pixel output will toggle between the specified sequence and allOff.

## Cheerlights / Custom color

New custom color option. You can create (or use an external program) a file called customlight.cfg. This file should contain a single color or list of colors (one color per line). They should be in html RRGGBB color format, with or without a #. 
Any lines not recognised are ignored.

To use in automation use the word "custom" in place of the RGB value in the URL string.

For best effect use either a single color in the customlight.cfg file, or the same number of custom entries as the number of custom LEDs selected.

## Cheerlight automation

If you would like to have the lights automatically update to the latest cheerlight color then you can add the following line to crontab.

    */5 * * * * wget -O ~/pixel-server/customlight.cfg http://api.thingspeak.com/channels/1417/field/2/last.txt

The ~ assumes that this is installed in your home directory.
    
# Configuration

The default configuration is in a file called **defaults.cfg**. You should not edit that file directly as it will be overwritten by future upgrades. Instead copy the relevant entries to a new file called **pixelserver.cfg**.

The following parameters can be used:

* ledcount - Number of LEDs on your pixel strip
* gpiopin - GPIO pin number
* ledfreq - LED frequency (normally leave at default)
* leddma - LED DMA number (normally leave at default)
* ledchannel - LED channel number (normally leave at default)
* ledmaxbrighness - LED brightness (0 to 255)
* ledinvert - Set to True if an inverting buffer is used (otherwise False)
* striptype - Set to colour sequence or strip type

## Valid strip types
The striptype can be set using a color sequence. For WS2811 / WS2812B strips then this should be three letters representing the order of the RGB colours eg. _GRB_ for green, red then blue.

For SK6812 strips then it should be four letters also including W for white. eg. _GRBW_ for green, red, blue and then white.

Alternatively the strip type can be defined as one of the following values:  
WS2811_STRIP_RGB  
WS2811_STRIP_RBG  
WS2811_STRIP_GRB  
WS2811_STRIP_BGR  
WS2811_STRIP_BRG  
WS2811_STRIP_BGR  
WS2812_STRIP  
SK6812_STRIP_RGBW  
SK6812_STRIP_RBGW  
SK6812_STRIP_GRBW  
SK6812_STRIP_GBRW  
SK6812_STRIP_BRGW  
SK6812_STRIP_BGRW  
SK6812_STRIP  
SK6812W_STRIP  


# Updates and changes

This code is in development and may change in operation. Details of significant changes will be included here.

# Change log

## May 2022
Additional color option of "Custom Color". This allows custom colors to be used through a custom.light.cfg file. This is particularly useful if you want to be able to control color using cheerlights or would like to provide your own home automation with non-volitile color changes.


## April 2022
When setting a sequence the server will now respond with a JSON formatted status replacing the previous single word "ready" or simple error message. This provides feedback on the status of the request as well as what sequence is currently being displayed.

    
# Upgrading to the latest version

If you installed the software using a _git clone_ then you can update by issuing a `git pull`. Alternatively you can download the latest version overwriting your existing files manually.

As long as you followed the instructions regarding using a custom configuration file, then your config will still be kept.



