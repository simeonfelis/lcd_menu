lcd_menu
========

A tiny lcd info and menu for the 16x2 lcd display for raspberry from adafruit.

Find pictures and videos in the wiki: https://github.com/simeonfelis/lcd_menu/wiki

It has capabilities to play internet radio streams using vlc. Therefor it 
read the playlist in /home/pi/playlist.m3u (by default)

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

Make sure the user pi is added to group audio!

    usermod -a -G audio pi



Details
=======

This is how a playlist can look like:

    cat playlist.m3u
    #EXTM3U
    #EXTINF:0,Secret Agent: The soundtrack for your stylish - Secret Agent: The soundtrack for your stylish, mysterious, dangerous life. For Spys and P.I.'s too! [SomaFM]
    http://mp2.somafm.com:9016
    #EXTINF:0,Charivari Regensburg
    #EXTVLCOPT:network-caching=1000
    http://edge.live.mp3.mdn.newmedia.nacamar.net/ps-chari/livestream.mp3
    #EXTINF:0,Bayern 2 Sued
    #EXTVLCOPT:network-caching=1000
    http://br-mp3-bayern2sued-m.akacast.akamaistream.net/7/731/256282/v1/gnl.akacast.akamaistream.net/br_mp3_bayern2sued_m


Playlist and user
-----------------

VLC must not be run as root. I use the `su` command to switch the user for VLC. Change the user with the ``-u`` flag on RPi_lcdloop.py

The location of the playlist.m3u can be provided with ``-p`` flag to RPi_lcdloop.py. Modify it accordingly in your systemd service file.

See also

    # RPi_lcdloop.py -h
    usage: RPi_lcdloop.py [-h] [-u USER] [-p PLAYLIST] [-d]

    Program to provide little Menu for Adafruit's LCD menu

    optional arguments:
      -h, --help            show this help message and exit
      -u USER, --user USER  user VLC should be run as. Default: pi
      -p PLAYLIST, --playlist PLAYLIST
                            Playlist for VLC. Default: /home/pi/playlist.m3u
      -d, --daemon          continue after crashes

     Example: RPi_lcdloop --user pi --playlist /path/to/playlist.m3u -d



Instanciate the menu by calling

    sudo python RPi_lcdloop.py

To start the menu during boot put following in `/etc/rc.local` (or use the systemd service file):

    PATH=$PATH:/usr/bin:/usr/local/bin:/bin:/usr/sbin
    export PATH
    (python /path/to/RPi_lcdloop.py --daemon) &


To start the menu manually start it without the `--daemon` parameter.

I made a smbd share for the playlist and edit with VLC on my normal PC.

