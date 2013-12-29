lcd_menu
========

A tiny lcd info and menu for the 16x2 lcd display for raspberry from adafruit.

It has capabilities to play internet radio streams using vlc. Therefor it 
read the playlist in /home/simeon/playlist.pls.

The volume can be controlled, to.

You can see local lan IP address and the public ip address.


This LCD menu structure is kept simple, stupid and dump. It is not really good code,
although it should just work and can be extended without reading too much. Assume the
writer of the code did not had much time of thinking an nice architecture and you
will find your way pretty quickly.


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
 * i2c-tools (on ArchLinux)

Make sure the corresponding modules are loaded:

    modprobe i2c-bcm2708
    modprobe i2c-dev

or

    cat /etc/modules-load.d/raspberry.conf
    bcm2708-rng
    snd-bcm2835
    i2c-bcm2708
    i2c-dev


On systemd-driven systems (like ArchLinux), you can use the lcd.service file and place it here:

    cp lcd.service /usr/lib/systemd/system/lcd.service
    # modify paths in lcd.service accordingly!
    systemctl daemon-reload
    systemctl enable lcd
    systemctl start lcd


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

This is how a playlist can look like:

    cat playlist.plx
    [playlist]
    numberofentries=2
    File1=http://mp2.somafm.com:9016
    Title1=SomaFM: Secret Agent (#1 128k mp3): The soundtrack for your stylish, mysterious, dangerous life. For Spies and PIs too!
    Length1=-1
    File2=http://ice.somafm.com/secretagent
    Title2=SomaFM: Secret Agent (Firewall-friendly 128k mp3) The soundtrack for your stylish, mysterious, dangerous life. For Spies and PIs too!
    Length2=-1
    Version=2

The location of the playlist.pls is hardcoded in the Menu.py file. Modify it accordingly.

VLC must not be run as root. I use the `su` command to switch the user for VLC. Change the user in Menu.py.
Furthermore the `vlc -I rc` option is used to control VLC.


Instanciate the menu by calling

    sudo python RPi_lcdloop.py daemon

To start the menu during boot put following in `/etc/rc.local` (or use the systemd service file):

    PATH=$PATH:/usr/bin:/usr/local/bin:/bin:/usr/sbin
    export PATH
    (python /path/to/RPi_lcdloop.py daemon) &


To start the menu manually start it without the `daemon` parameter.


