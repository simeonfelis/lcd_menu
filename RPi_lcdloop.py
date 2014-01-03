#!/usr/bin/python

import sys, os, signal
import socket
from time import sleep

from Menu import *

# import Adafruit path

CUR_DIR = os.path.dirname(__file__)

# I have adafruit stuff one folder relative up

ADAFRUIT_DIR = os.path.join(CUR_DIR, "..", "Adafruit-Raspberry-Pi-Python-Code")
ADAFRUIT_LCD_PLATE = os.path.join(ADAFRUIT_DIR, "Adafruit_CharLCDPlate")

sys.path.append(ADAFRUIT_DIR)
sys.path.append(ADAFRUIT_LCD_PLATE)

lcd = None # global for lcd menu to make signal handling easier

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate


class LcdMenu(Adafruit_CharLCDPlate):
    
    _system_stoped = False

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
            if self._system_stoped:
                self.menu._system_stoped = True
                raise KeyboardInterrupt
            sleep(0.3)
            update = False
            if self.buttonPressed(self.SELECT):
                self.menu = self.menu.select_press(ref=self.buttonPressed, btn=self.SELECT)
                update = True
            elif self.buttonPressed(self.LEFT):
                self.menu = self.menu.left_press(ref=self.buttonPressed, btn=self.LEFT)
                update = True
            elif self.buttonPressed(self.RIGHT):
                self.menu = self.menu.right_press(ref=self.buttonPressed, btn=self.RIGHT)
                update = True
            elif self.buttonPressed(self.DOWN):
                self.menu = self.menu.down_press(ref=self.buttonPressed, btn=self.DOWN)
                update = True
            elif self.buttonPressed(self.UP):
                self.menu = self.menu.up_press(ref=self.buttonPressed, btn=self.UP)
                update = True
            else:
                if self.menu.update():
                    update = True
            if update:
                self.clear()
                self.message(self.menu.text)

def make_menuitems():
    menu_playlist = MenuPlaylist()
    menu_volume = MenuVolume("Volume")
    menu_lan_ip = MenuLanIp("lan ip")
    menu_public_ip = MenuPublicIp("public ip")
    menu_shutdown = MenuShutdown()
    menu_reboot = MenuReboot()
    
    #all_items = [menu_init, menu_playlist, menu_volume, menu_lan_ip, menu_public_ip, menu_shutdown, menu_reboot]
    all_items = [menu_playlist, menu_volume, menu_lan_ip, menu_public_ip, menu_shutdown, menu_reboot]
    return all_items

def run_shit(menuitems):
    
    global lcd

    for i, m in enumerate(menuitems):
         if i < len(menuitems)-1:
             menuitems[i].right = menuitems[i+1]
         if i:
             menuitems[i].left = menuitems[i-1]


    # Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
    # pass '0' for early 256 MB Model B boards or '1' for all later versions
    
    #lcd = LcdMenu(menu=menu_init)
    lcd = LcdMenu(menu=menuitems[0])
    
    # Clear display and show greeting, pause 1 sec
    lcd.clear()
    
    lcd.backlight(lcd.GREEN)

    lcd.loop()

def onShutdown(signum, stack):
    print "GOT SHUTDOWN REQUEST"
    global lcd
    lcd.backlight(lcd.BLUE)
    lcd.clear()
    lcd.message("LCD MENU STOPED")
    lcd._system_stoped = True
    
if __name__ == "__main__":

    signal.signal(signal.SIGTERM, onShutdown)
    signal.signal(signal.SIGUSR1, onShutdown)

    menuitems = make_menuitems()

    if "daemon" in sys.argv:
        while True:
            try:
                run_shit(menuitems)
            except KeyboardInterrupt:
                break
            except Exception, e:
                lcdFallback = Adafruit_CharLCDPlate()
                lcdFallback.clear()
                lcdFallback.backlight(lcdFallback.RED)

                mes = repr(e)
                if len(mes)>16:
                    mes = mes[:16] + "\n" + mes[16:]

                lcdFallback.message(mes)

                print "Exception", e
                sleep(10)
                del lcdFallback

    else:
       run_shit(menuitems)

