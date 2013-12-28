lcd_menu
========

A tiny lcd info and menu for the 16x2 lcd display for raspberry from adafruit.

It has capabilities to play internet radio streams using vlc. Therefor it 
fetches data from `http://localhost/list/`.

The volume can be controlled, to.

You can see local lan IP address and the public ip address.

This menu requires the Adafruit Raspberry code. Following patch is required:

    diff --git a/Adafruit_I2C/Adafruit_I2C.py b/Adafruit_I2C/Adafruit_I2C.py
    index 3423461..a7df93a 100755
    --- a/Adafruit_I2C/Adafruit_I2C.py
    +++ b/Adafruit_I2C/Adafruit_I2C.py
    @@ -6,7 +6,7 @@ import smbus
     # Adafruit_I2C Class
     # ===========================================================================
     
    -class Adafruit_I2C :
    +class Adafruit_I2C(object) :
     
       @staticmethod
       def getPiRevision():

Install
=======

Following packages should be installed:

 * vlc
 * alsa-utils
 * git
 * python-smbus (on debian)
 * i2c-tools (on archlinux)

Make sure the corresponding modules are loaded:

    modprobe i2c_bcm2708
    modprobe i2c-dev


Get the Adafruit code, this code:

    git clone https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git
    git clone https://github.com/simeonfelis/lcd_menu.git

Patch the Adafruit code:

    cd Adafruit-Raspberry-Pi-Python-Code
    git apply ../lcd_menu/adafruit.patch
    cd -

Start the lcd-menu:

    cd lcd_menu
    sudo python RPi_lcdloop.py



Details
=======

The format of internet radio stream list that is fetched from
`http://localhost/list/` is a json encoded list like that:

    [
      {"url": "http://stream1.example.com", "name": "Stream name"},
      {"url": "http://stream2.example.com", "name": "Another stream name"},
      ...
    ]

I created a little django project to achieve that. If somebody is interested, I
can publish it, too.

Instanciate the menu by calling

    sudo python RPi_lcdloop.py daemon

To start the menu during boot put following in `/etc/rc.local`:

    PATH=$PATH:/usr/bin:/usr/local/bin:/bin:/usr/sbin
    export PATH
    (sudo python /path/to/RPi_lcdloop.py daemon) &


To start the menu manually start it without the `daemon` parameter.



