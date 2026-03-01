import subprocess
import io
from pyvirtualdisplay import Display
from .utils import get_value_or_default, load_config


class Screen:
    def __init__(self, screen_params=None):
        self.screen_params = screen_params
        self.visible = 1
        self.height = 1200
        self.width = 800
        self.display = None
        if self.screen_params:
            self.parse_screen_params()

    def parse_screen_params(self):
        self.screen_params = load_config(self.screen_params)
        self.visible = get_value_or_default(self.screen_params.get("screen_visible"), self.visible)
        self.height = get_value_or_default(self.screen_params.get("screen_height"), self.height)
        self.width = get_value_or_default(self.screen_params.get("screen_width"), self.width)
    
    def screenshot_screen(self):
        screenshot_process = subprocess.run(
        ["import", "-window", "root", "png:-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL)
        if not screenshot_process.stdout:
                raise ValueError("Empty Screenshot")

        image_bytes = io.BytesIO(screenshot_process.stdout)
        image_bytes.seek(0)
        return image_bytes
    
    def launch_screen(self):
        self.display = Display(visible=self.visible, size=(self.width, self.height))
        self.display.start()
        return self
    
    def stop_screen(self):
        self.display.stop()