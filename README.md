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

For more information see: <http://www.penguintutor.com/raspberrypi/startup>

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

For SK6812 strips then it should be four leteers also including W for white. eg. _GRBW_ for green, red, blue and then white.

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

    
# Upgrading to the latest version

If you installed the software using a _git clone_ then you can update by issuing a `git pull`. Alternatively you can download the latest version overwriting your existing files manually.

As long as you followed the instructions regarding using a custom configuration file, then your config will still be kept.



