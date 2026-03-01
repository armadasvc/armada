import time, subprocess, random, os
from .virtual_cursor_path import VirtualCursorPath
from .random_sleeper import rsleep

    
class XdoToolActions:
    def __init__(self,show_cursor,emulate_movement):
        self.show_cursor = show_cursor
        self.emulate_movement = emulate_movement

    def xsend_xdo(self,current_position,x,y,width,height,viewport_width,viewport_height,sleep_array,text,proportion=None):
        sleep_before,sleep_after = sleep_array
        self.xclick_xdo(current_position,x,y,width,height,viewport_width,viewport_height,sleep_array,proportion)
        rsleep(sleep_before)
        self.xfill_xdo(text)
        rsleep(sleep_after) 
        return [x,y]
    
    def xclick_xdo(self, current_position,x,y, width,height,viewport_width,viewport_height,sleep_array,proportion=None):
        sleep_before, sleep_after = sleep_array
        self.emulate_movement = True #
        if self.emulate_movement:
            if proportion:
                x = x + proportion[0]*width
                y = y + proportion[1]*height
        new_cursor_position = self.xmove_xdo(current_position, x,y,viewport_width,viewport_height)
        rsleep(sleep_before)
        XdoToolBasicActions().xdo_click()
        rsleep(sleep_after)
        return new_cursor_position

    @staticmethod
    def xfill_xdo(text):
        interval_min = random.uniform(0.01, 0.09)
        interval_max = random.uniform(0.1, 0.7)
        for i in text:
            sleeping_delay = random.uniform(interval_min, interval_max)
            rsleep(sleeping_delay, activate_random=False)
            time.sleep(0.01)
            XdoToolBasicActions.xdo_send_key(i)
            time.sleep(0.02)

    def xmove_xdo(self,current_position,x,y,viewport_width,viewport_height):
        desired_position = [x,y]
        path = VirtualCursorPath().get_virtual_cursor_path(current_position,desired_position,viewport_width,viewport_height)

        if self.show_cursor:
            cursor_illustration = XdoToolCursorIllustration()
            cursor_illustration.initialize_cursor_illustration(current_position)

        for i in range(len(path[0])):
            XdoToolBasicActions().xdo_move(path,i)
            time.sleep(0.01)

            if self.show_cursor:
                cursor_illustration.move_cursor_illustration(path,i)

        if self.show_cursor:
            cursor_illustration.kill_cursor_illustration()
        return desired_position

class XdoToolBasicActions:
    XDOTOOL_KEY_REPLACEMENT = {
        ".": "period", ",": "comma", "-": "minus", "_": "underscore",
        "+": "plus", "=": "equal", "/": "slash", "\\": "backslash",
        ":": "colon", ";": "semicolon", "'": "apostrophe", "\"": "quotedbl",
        "(": "parenleft", ")": "parenright", "[": "bracketleft", "]": "bracketright",
        "{": "braceleft", "}": "braceright", "!": "exclam", "@": "at",
        "#": "numbersign", "$": "dollar", "%": "percent", "^": "asciicircum",
        "&": "ampersand", "*": "asterisk", "~": "asciitilde", "|": "bar",
        "<": "less", ">": "greater", "?": "question", "§": "section",
        "€": "EuroSign", " ": "space"
    }

    def __init__(self):
        pass

    @staticmethod
    def get_window_id(window_name: str) -> str | None:
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", window_name],
                capture_output=True,
                text=True,
                check=True
            )

            window_ids = result.stdout.strip().splitlines()
            return window_ids[0] if window_ids else None

        except subprocess.CalledProcessError:
            return None
    
    @staticmethod
    def xdo_send_key(key):
        key = XdoToolBasicActions.XDOTOOL_KEY_REPLACEMENT.get(key,key)
        subprocess.run(["xdotool","key",str(key)])

    @staticmethod
    def xdo_click():
        subprocess.run(["xdotool", "click", "1"])
    
    @staticmethod
    def xdo_move(path,step):
        subprocess.run(["xdotool", "mousemove", str(path[0][step]),str(path[1][step])])
    
from PIL import Image
def create_red_square(file_name="red_square.png"):
    # Create a new 20×20 pixel image, in RGB mode, filled with red.
    image = Image.new("RGB", (20, 20), (255, 0, 0))
    # Save the image in the current directory.
    image.save(file_name)   

class XdoToolCursorIllustration:
    def __init__(self):
        self.window_cursor_id = None

    def initialize_cursor_illustration(self,current_position):
        create_red_square()
        x,y = current_position
        os.system(f"feh red_square.png --geometry +{str(x)}+{str(y)} &")
        time.sleep(0.05)
        self.window_cursor_id = subprocess.check_output(["xdotool", "search", "--name", "red_square"], text=True).strip()
        time.sleep(0.05)

    def move_cursor_illustration(self,path,move_number):
        subprocess.run(["xdotool", "windowmove", self.window_cursor_id,str(path[0][move_number]),str(path[1][move_number])])
    
    @staticmethod
    def kill_cursor_illustration():
        os.system("pkill feh")
        os.remove("red_square.png")