#!/usr/bin/python

import sys, os
import socket
from time import sleep


# import Adafruit path

CUR_DIR = os.path.dirname(__file__)

# I have adafruit stuff one folder relative up

ADAFRUIT_DIR = os.path.join(CUR_DIR, "..", "Adafruit-Raspberry-Pi-Python-Code")
ADAFRUIT_LCD_PLATE = os.path.join(ADAFRUIT_DIR, "Adafruit_CharLCDPlate")

sys.path.append(ADAFRUIT_DIR)
sys.path.append(ADAFRUIT_LCD_PLATE)


from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate


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
            elif self.buttonPressed(self.DOWN):
                self.clear()
                self.menu = self.menu.down_press(ref=self.buttonPressed, btn=self.DOWN)
                self.message(self.menu.text)
            elif self.buttonPressed(self.UP):
                self.clear()
                self.menu = self.menu.up_press(ref=self.buttonPressed, btn=self.UP)
                self.message(self.menu.text)
            


def run_shit():


    menu_init = LcdState("init")
    menu_playlist = MenuPlaylist("playlist")
    menu_volume = MenuVolume("Volume")
    menu_lan_ip = MenuLanIp("lan ip")
    menu_public_ip = MenuPublicIp("public ip")
    
    all_items = [menu_init, menu_playlist, menu_volume, menu_lan_ip, menu_public_ip]
    
    for i, m in enumerate(all_items):
         if i < len(all_items)-1:
             all_items[i].right = all_items[i+1]
         if i:
             all_items[i].left = all_items[i-1]


    # Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
    # pass '0' for early 256 MB Model B boards or '1' for all later versions
    lcd = LcdMenu(menu=menu_init)
    
    # Clear display and show greeting, pause 1 sec
    lcd.clear()
    
    
    lcd.backlight(lcd.GREEN)
    lcd.message(get_lan_ip()+'\n'+get_public_ip())
    sleep(1)


    lcd.loop()

if __name__ == "__main__":

    from Menu import *


    if "daemon" in sys.argv:
        while True:
            try:
                run_shit()
            except KeyboardInterrupt:
                break
            except Exception, e:
                lcd = Adafruit_CharLCDPlate()
                lcd.clear()
                lcd.backlight(lcd.RED)

                mes = repr(e)
                if len(mes)>16:
                    mes = mes[:16] + "\n" + mes[16:]

                lcd.message(mes)

                print "Exception", e
                sleep(10)

    else:
       run_shit()
    
