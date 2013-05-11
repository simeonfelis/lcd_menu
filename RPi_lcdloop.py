#!/usr/bin/python

import sys, os


# import Adafruit path

CUR_DIR = os.path.dirname(__file__)

# I have adafruit stuff one folder relative up

ADAFRUIT_DIR = os.path.join(CUR_DIR, "..", "Adafruit-Raspberry-Pi-Python-Code")
ADAFRUIT_LCD_PLATE = os.path.join(ADAFRUIT_DIR, "Adafruit_CharLCDPlate")

sys.path.append(ADAFRUIT_DIR)
sys.path.append(ADAFRUIT_LCD_PLATE)


import socket

import os
from time import sleep
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate


if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])


def get_public_ip(timeout=2):
    # get public address
    import httplib

    c = httplib.HTTPConnection("checkip.dyndns.com", timeout=timeout)
    try:
        c.request("GET", "/")
    except socket.gaierror:
        return "no conn to dynds"

    htmlbody=c.getresponse().read()
    c.close()

    import re

    public_ip_match = re.match(r'.*\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}).*', htmlbody)

    if public_ip_match:
        return public_ip_match.group(1)
    else:
        return "dynds wrong reply"


def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


class LcdState():
    def __init__(self, text, left=None, right=None, up=None, down=None):
        self.text = text
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        if type(self.left) == LcdState:
            self.left.right = self

    def action(self):
        # overwrite this function when sublassing
        return self

    def select_press(self, ref, btn):
        while(ref(btn)): pass
        return self.action()

    def left_press(self, ref, btn):
        if self.left:
            while(ref(btn)): pass
            return self.left
        else:
            while(ref(btn)): pass
            return self

    def right_press(self, ref, btn):
        if self.right:
            while(ref(btn)): pass
            return self.right
        else:
            while(ref(btn)): pass
            return self

    def up_press(self):
        pass

    def down_press(self):
        pass

class MenuLanIp(LcdState):
    def action(self):
        # get old text
        text = self.text.split("\n")[0]
        self.text = text + "\n" + get_lan_ip()
        return self

class MenuPublicIp(LcdState):
    def action(self):
        # get old text
        text = self.text.split("\n")[0]
        self.text = text + "\n" + get_public_ip()
        return self


menu_init = LcdState("init")
menu_lan_ip = MenuLanIp("lan ip")
menu_public_ip = MenuPublicIp("public ip")

menu_public_ip.left = menu_lan_ip
menu_lan_ip.right = menu_public_ip
menu_lan_ip.left = menu_init
menu_init.right = menu_lan_ip



class LcdMenu(Adafruit_CharLCDPlate):

    def __init__(self, *args, **kwargs):

        if "menu" in kwargs:
            self.menu = kwargs.pop("menu")
        else:
            raise KeyError("menu argument required")

        super(LcdMenu, self).__init__(*args, **kwargs)


    def loop(self):
        self.clear()
        self.message(self.menu.text)
        while True:
            if self.buttonPressed(self.SELECT):
                self.clear()
                self.menu = self.menu.select_press(ref=self.buttonPressed, btn=self.SELECT)
                self.message(self.menu.text)
            elif self.buttonPressed(self.LEFT):
                self.clear()
                self.menu = self.menu.left_press(ref=self.buttonPressed, btn=self.LEFT)
                self.message(self.menu.text)
            elif self.buttonPressed(self.RIGHT):
                self.clear()
                self.menu = self.menu.right_press(ref=self.buttonPressed, btn=self.RIGHT)
                self.message(self.menu.text)
            

# Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
lcd = LcdMenu(menu=menu_init)

# Clear display and show greeting, pause 1 sec
lcd.clear()


lcd.backlight(lcd.GREEN)
lcd.message(get_lan_ip()+'\n'+get_public_ip())
sleep(1)

lcd.loop()

#while True:
#    try:
#        lcd.loop()
#    except KeyboardInterrupt:
#        break
#    except Exception, e:
#        lcd = LcdMenu(menu=menu_init)
#        print "Exception", e

