#!/usr/bin/python


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

    with c=httplib.HTTPConnection("checkip.dyndns.com", timeout=timeout):
        try:
            c.request("GET", "/")
        except socket.gaierror:
            return "no conn to dynds"

        htmlbody=c.getresponse().read()

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

# Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
lcd = Adafruit_CharLCDPlate()

# Clear display and show greeting, pause 1 sec
lcd.clear()


lcd.backlight(lcd.GREEN)
lcd.message(get_lan_ip()+'\n'+get_public_ip())
sleep(1)
