# pixel-server
Wireless control of PixelStrips or NeoPixels using a web graphical interface running on a Raspberry Pi.

Works with any Raspberry Pi.
On older Raspberry Pi models (Raspberry Pi V1 or Raspberry Pi Zero) then it is recommended running in headless mode and without using a local web browser. For newer models that should not be necessary.

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

    pip3 install rpi_ws281x

To install the Argon hash algorithm

    sudo apt install python3-argon2

To install the Flask CSRF protection

    pip3 install Flask-WTF

To be able to run the tests

    sudo apt install python3-pytest


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

The pixel server is designed to support varying levels of security depending upon your system requirements.

If used on a private only network then it can be configured for network address authentication.

If allowing incoming connections from the Internet then it is recommended that user authentication is enabled and it is configured through SSL. The configuration below is based on using Nginx as a reverse proxy to provide HTTPS using a LetsEncrypt certificate.

## Enable SSL (HTTPS)

This explains how you can use the Flask (development) server with https using Nginx as a reverse proxy. This uses a free security certificate from [Let's Encrypt](https://letsencrypt.org/). This means that I am able to setup Nginx as a reverse proxy on my home server, which could be used to provide encrypted connections to different services.


### On Nginx reverse proxy

This does not have to be on the same server as pixel-server.

First make sure your system is up-to-date

sudo apt update
sudo apt upgrade
sudo apt install nginx

sudo apt install certbot
sudo apt install python3-certbot-nginx


add new file in sites-available

ln -s to /etc/nginx/sites-enabled


Add the following in a location file (this assumes using /rpi1/ as the route
for this particular server.

    location /rpi1/ {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass http://<pixelserver_address>/;
    }


sudo certbot --nginx -d <public hostname>

This updates /etc/nginx/sites-enabled

update with
sudo nginx -t
sudo nginx -s reload

Add the following to crontab for root:
0 12 * * * /usr/bin/certbot renew --quiet

This checks for updates on a daily basis and if required renew


## Login

New login features requires that users login to the web interface. This would prevent automation from working, therefore an alternative is allowed where clients can be pre-authorized based on their IP address. All admin functions need to be logged in as an admin user.

If automation runs on the local machine then it is recommended that only the loopback IP address 127.0.0.1 is pre-authorized, but additional IP addresses can be enabled for use by WiFi switches, such as those used in the [ESP32 wireless capacitive touch switch](http://www.penguintutor.com/projects/esp32-captouch).


There are no users setup as default. Before you can login then you should create your first admin user with the following command:

    python3 createadmin.py <username> <password> >> users.cfg

The angled brackets should not be included around the username or password. The double greater than symbols will append to the users.cfg file, so if the file already exists this will not remove any existing accounts. Ensure you don't end up with multiple users with the same username using this command. Instead once you have setup the initial user you should login through the web interface to configure additional users.

### Docker install

If you wish to use this project in a container, you can do so by entering the following commands:

    cd ~
    sudo mkdir pixel-server
    sudo chown $USER: pixel-server
    git clone https://github.com/penguintutor/pixel-server.git pixel-server

Make sure to make changes to your config file, so that the pixel-server knows how to communicate with your neopixel device!

    docker build . -t pixel-server
    docker run --restart unless-stopped --privileged -p 80:80 pixel-server

This will make the project run on port 80/HTTP and also start on boot.
To update the container, enter the following commands:

    docker stop pixel-server
    docker rm pixel-server
    cd ~/pixel-server/
    git pull
    docker build . -t pixel-server
    docker run --restart unless-stopped --privileged -p 80:80 pixel-server
    

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


# Auth.cfg
Controls authentication. Can have one or more of the following, which can be a single IP address, or a network subnet, multiple addresses or network subnets (comma seperated) or 0.0.0.0 (all addresses)
Multiple entries will be appended to the access.

proxy_server =
Any addresses in this range will be treated as proxy servers.
If the proxy server has X-Real-IP set then that will be used instead of the local ip address of the server. Warning if that is not a proxy server then this
could be a security risk (in terms of allowing non authenticated logins). Cannot be 0.0.0.0 (everywhere is a proxy doesn't make sense) - normally this will be specific IP address rather than range.
If the attempt from the proxy server does not have X-Real_IP then the address will be treated as coming from that IP address.


network_allow_always =
Allways allow without login (useful for automation or local)

network_allow_auth =
Must always be a logged in user to change the light status
normally this is 0.0.0.0 = allow all, but with authentication

Note that to perform any adminstration tasks then must be in either of the above - but must also be authenticated.


# Updates and changes

This code is in development and may change in operation. Details of significant changes will be included here.

# Change log

## August 2022 - v0.1.0
Authentication merged into main branch. 

## July 2022
Authentication and logging enabled. This is a significant change which brings in additional security. Changes may be needed to user configuration files as well as generating a new user to administer the system.

You may need to install additional libraries including the following commands:

    sudo pip3 install rpi_ws281x
    sudo apt install python3-argon2
    sudo pip3 install Flask-WTF



## May 2022
Additional color option of "Custom Color". This allows custom colors to be used through a custom.light.cfg file. This is particularly useful if you want to be able to control color using cheerlights or would like to provide your own home automation with non-volitile color changes.


## April 2022
When setting a sequence the server will now respond with a JSON formatted status replacing the previous single word "ready" or simple error message. This provides feedback on the status of the request as well as what sequence is currently being displayed.


# Upgrading to the latest version

If you installed the software using a _git clone_ then you can update by issuing a `git pull`. Alternatively you can download the latest version overwriting your existing files manually.

As long as you followed the instructions regarding using a custom configuration file, then your config will still be kept.

If upgrading from a version prior to September 2022 then you may need to create a new configuration file for auth.cfg and a new users.cfg file using createadmin.py

# Development

## Testing

Currently supports limited automated testing based around the authentication. This is achieved using:
    py.test-3

Manual testing is required for all other functions.
