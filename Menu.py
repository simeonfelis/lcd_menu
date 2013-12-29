import os, socket
from time import sleep
from subprocess import Popen, PIPE

VLC_USER = "simeon"
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

    def up_press(self, ref, btn):
        return self

    def down_press(self, ref, btn):
        return self

class MenuShutdown(LcdState):
    def action(self):
        text = self.text.split("\n")[0]
        self.text = text + "\n" + "shutting down..."
        cmd = ["shutdown", "-h", "now"]
        Popen(cmd, stdin=PIPE, stdout=PIPE, preexec_fn=os.setsid)
        

class MenuLanIp(LcdState):
    """Displays lan IP address when select is pressed"""

    def action(self):
        # get old text
        text = self.text.split("\n")[0]
        self.text = text + "\n" + get_lan_ip()
        return self

class MenuPublicIp(LcdState):
    """Displays public IP address when select is pressed"""

    def action(self):
        # get old text
        text = self.text.split("\n")[0]
        self.text = text + "\n" + get_public_ip()
        return self


class MenuPlaylist(LcdState):
    """Load a list of URLs for internet radio streams to play. Assumes
    such list is provided on http://localhost/list, and the return value
    is a json encoded list in the format::

        [
          {"url": "http://stream1.example.com", "name": "Stream name"},
          {"url": "http://stream2.example.com", "name": "Another stream name"},
        ]

    When select is pressed, it fetches the list from Server. Then a stream can
    be chosen by pressing up/down. When select is pressed, it plays the stream.
    When select is pressed again, the stream will be stoped.

    VLC is used as player.

    """

    lists = []
    pos = -1
    play = -1
    ps = None

    def __init__(self, *args, **kwargs):

        super(MenuPlaylist, self).__init__(*args, **kwargs)

        # Try to load list on startup
        cmd = ["su", "-c", "vlc -I rc %s" % (VLC_PLAYLIST), VLC_USER]
        self.ps = Popen(cmd, stdout=PIPE, stdin=PIPE, preexec_fn=os.setsid)
        sleep(3)
        # dump two info lines
        self.ps.stdout.readline(); self.ps.stdout.readline()
        sleep(3)
        self.action()

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
    
    def read_vlc_result(self):
        tmp = self.ps.stdout.readline().strip()
        print "GOT: '%s'" % tmp
        while tmp.startswith('>'):
            tmp = tmp.lstrip('>').strip()
        tmp = tmp.strip()
        return tmp

    def write_vlc_command(self, command):
        self.ps.stdin.write("%s\n" % command)

    def action(self):
        print "Playlist action"
        self.write_vlc_command("is_playing")
        res = self.read_vlc_result()
        if res == "1":
            self.text = "select to stop vlc"
            self.write_vlc_command("stop")
        elif res == "0":
            self.text = "select to start vlc"
            self.write_vlc_command("play")
            return self
        else:
            raise ValueError("unexpected vlc state: '%s'" % str(res))

        return self


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


