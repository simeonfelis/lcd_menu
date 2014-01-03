import os, socket
from time import sleep
from subprocess import Popen, PIPE

VLC_USER = "pi"
VLC_PLAYLIST = os.path.join("/", "home", VLC_USER, "playlist.pls")

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
    except socket.error:
        return "server offline?"
    except httplib.CannotSendRequest:
        return "connection error"
    except httplib.HTTPException:
        return "http error"

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

class LcdState(object):
    """Basic class for a LCD menu item. Default behavior:
        
        All button press events are actions. Every action returns
        the same (evt. updated) object instance or a different one.

        It is intended to subclass the LcdState class and overwrite
        the select_press(ref, btn), up_press(ref, btn) and down_press(ref, btn)
        functions.

        The left_press(ref, btn) and right_press(ref, btn) will return the next
        menu item instance in the menu if exists. Otherwise it returns the same
        instance.

        The arguments ref and btn are to poll the button if it is still pressed.
        ref is a reference to buttonPressed() function from Adafruit library, which
        requires the button to poll as argument. To wait until a button is released
        you could do something like that::

             while(ref(btn)): pass


        You can init a flat menu structure e.g. like that:: 

            all_items = [menu_item_1, menu_item_2, menu_item_3]
            for i, m in enumerate(all_items):
                 if i < len(all_items)-1:
                     all_items[i].right = all_items[i+1]
                 if i:
                     all_items[i].left = all_items[i-1]


        This makes sure every item is connected with each other.

    """
    
    _system_stoped = False
    
    text = "1st line not set\n2nd line not set"

    def __init__(self, text=None, left=None, right=None, up=None, down=None):
        if text != None:
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

    def up_press(self, ref, btn):
        return self

    def down_press(self, ref, btn):
        return self
    
    def update(self):
        """
        Make this return False to reduce flickering"
        """
        return True

class MenuReboot(LcdState):
    text = "reboot RPi"
    def action(self):
        text = self.text.split("\n")[0]
        self.text = text + "\n" + "rebooting..."
        cmd = ["reboot"]
        Popen(cmd)
        return self
    
    def update(self):
        return False

class MenuShutdown(LcdState):
    text = "shutdown RPi"
    def action(self):
        text = self.text.split("\n")[0]
        self.text = text + "\n" + "shutting down..."
        cmd = ["shutdown", "-h", "now"]
        Popen(cmd)
        return self
    
    def update(self):
        return False
        

class MenuLanIp(LcdState):
    """Displays lan IP address when select is pressed"""

    def action(self):
        # get old text
        text = self.text.split("\n")[0]
        self.text = text + "\n" + get_lan_ip()
        return self
    
    def update(self):
        return False

class MenuPublicIp(LcdState):
    """Displays public IP address when select is pressed"""

    def action(self):
        # get old text
        text = self.text.split("\n")[0]
        self.text = text + "\n" + get_public_ip()
        return self
    
    def update(self):
        return False


class MenuPlaylist(LcdState):
    """Controls a VLC instance over its rc interface. By default, VLC opens
    a playlist located in VLC_PLAYLIST as user VLC_USER, because VLC will
    not run as root.
    
    Playlist items can be selected with up/down buttons. Select will start/stop VLC.
    """

    text = "Music player"

    lists = []
    pos = -1
    play = -1
    ps = None

    _update_counter = 0
    _shift_counter = 0

    

    def __init__(self, *args, **kwargs):
        
        if "user" in kwargs.keys():
            global VLC_USER
            VLC_USER = kwargs.pop("user")
        if "playlist" in kwargs.keys():
            global VLC_PLAYLIST
            VLC_PLAYLIST = kwargs.pop("playlist")

        super(MenuPlaylist, self).__init__(*args, **kwargs)
        
        self.start_vlc()
        
        self.settext()
        

    def down_press(self, ref, btn):

        while(ref(btn)): pass
        self.write_vlc_command("next")
        self.text = "vlc next"

        return self

    def up_press(self, ref, btn):
        
        while(ref(btn)): pass
        self.write_vlc_command("prev")
        self.text = "vlc previous"
        return self

    def get_title(self):
        if self.is_playing():
            self.write_vlc_command("get_title")
            firstline = self.read_vlc_result().replace('\n', "_")
        else:
            firstline = "Music player"
        
        return firstline
        
    def start_vlc(self):
        # Kill possibly existing vlc instances
        cmd = ["pkill", "vlc"]
        p = Popen(cmd)
        p.wait()

        # Try to load list on startup
        cmd = ["su", "-s", "/bin/bash", "-c", "vlc -I rc --no-playlist-autostart --one-instance --no-playlist-enqueue %s" % (VLC_PLAYLIST), VLC_USER]
        self.ps = Popen(cmd, stdout=PIPE, stdin=PIPE, preexec_fn=os.setsid)
        sleep(3)
        # dump two info lines
        self.ps.stdout.readline(); self.ps.stdout.readline()
        
        # looks like a bug with the command line parameters I have chosen. I need to write two times `play` after vlc started
        # to make VLC start playing. After VLC played once, it is working normally again.
        self.write_vlc_command("play")
        sleep(0.5)
        

    def settext(self, text=None):
        # scroll title
        title = self.get_title()
        if len(title) > 16:
            if self._shift_counter < 0:
                # fill the beginning with spaces
                self._shift_counter += 1
                spaces = -1 * self._shift_counter
                title = " "*spaces + title[0:16-spaces]
            elif self._shift_counter < len(title)-16:
                self._shift_counter += 1
                title = title[self._shift_counter:self._shift_counter+16]
            elif self._shift_counter < len(title):
                # fill rest with spaces to fully scroll complete title
                self._shift_counter += 1
                spaces = 16 - len(title) + self._shift_counter
                title = title[self._shift_counter:] + " "*spaces
                # actually, spaces are not needed for that effect
            else:
                # next time, start text from the very right
                self._shift_counter = -16
                title = " "*16
        firstline = title

        if text != None:
            self.text = firstline + "\n" + text
        else:
            if self.is_playing():
                duration = self.get_time()
                duration_back = duration
                try:
                    duration = int(duration)
                    minutes = duration/60
                    seconds = duration%60
                    duration = "%i:%02i" % (minutes, seconds)
                except Exception, e:
                    print "Exception while calculating elapsed playing time: %s" % str(e)
                    duration = duration_back
                spaces = 16 - len("playing") - len(duration)
                secondline = "playing" + " "*spaces + duration
            else:
                secondline = "stoped"
            self.text = firstline + "\n" + secondline
            
            
    def get_time(self):
        self.write_vlc_command("get_time")
        duration = self.read_vlc_result()
        return duration
    
    def read_vlc_result(self):
        try:
            tmp = self.ps.stdout.readline().strip()
        except IOError:
            if self._system_stoped:
                raise KeyboardInterrupt()
            print("VLC was shut down?")
            self.start_vlc()
            tmp = ""
        #print("GOT: %s" % tmp)
        while tmp.startswith('>'):
            tmp = tmp.lstrip('>').strip()
        tmp = tmp.strip()
        return tmp

    def write_vlc_command(self, command):
        try:
            self.ps.stdin.write("%s\n" % command)
        except IOError:
            if self._system_stoped:
                raise KeyboardInterrupt
            print("VLC was shut down?")
            self.start_vlc()
            raise ValueError("VLC shutdown?")

    def is_playing(self):
        self.write_vlc_command("is_playing")
        res = self.read_vlc_result()

        if res == "1":
            return True
        elif res == "0":
            return False
        else:
            raise ValueError("unexpected vlc state: '%s'" % str(res))

    def action(self):
        print "Playlist action"
        if self.is_playing():
            self.write_vlc_command("stop")
            sleep(.5)
            if self.is_playing():
                self.settext("could not stop")
            else:
                self.settext("stoped")
        else:
            self.write_vlc_command("play")
            sleep(.5)
            if self.is_playing():
                self.settext("playing")
            else:
                self.settext("could not start")

        return self
    
    def update(self):
        if not self.is_playing():
            return False
        
        self._update_counter += 1
        
        if self._update_counter == 2:
            self._update_counter = 0
            
            self.settext()
            
            return True

        return False 


class MenuVolume(LcdState):
    """
    Displays current volume setting. When up is pressed, volume
    is raised. If down is pressed, volume is lowered.

    Requires alsa-utils to be installed.
    """

    def __init__(self, *args, **kwargs):

        super(MenuVolume, self).__init__(*args, **kwargs)
        
        text = self.text.split("\n")[0]
        self.text = text + "\n" + self.get_volume()

    def get_volume(self):

        volume_text = "error"

        ps = Popen(["amixer", "--", "sget", "PCM"], stdout=PIPE)
        answer = ps.stdout.read()
        ps.wait()

        import re
        volume_match = re.match(r'.*\[([0-9]+%).*', answer, re.DOTALL)

        if volume_match:
            try:
                volume = int(volume_match.group(1)[:-1]) # leave out the percent sign
            except ValueError:
                volume_text = "int conv err"
            else:
                # make histogram
                volume_percent = int(16./100*volume)
                volume_text = "#"*volume_percent
            
        else:
            volume_text = "parse error"

        return volume_text
        
    def up_press(self, ref, btn):
        while(ref(btn)): pass
        ps = Popen(["amixer", "--", "sset", "PCM,0", "4dB+"], stdin=PIPE)
        ps.wait()

        text = self.text.split("\n")[0]
        self.text = text + "\n" + self.get_volume()
        return self

    def down_press(self, ref, btn):
        while(ref(btn)): pass
        ps = Popen(["amixer", "--", "sset", "PCM,0", "4dB-"], stdin=PIPE)
        ps.wait()

        text = self.text.split("\n")[0]
        self.text = text + "\n" + self.get_volume()
        return self


