import random
import asyncio
from nodriver import *
from .no_driver.IframeManager import *
from .no_driver.Geometry import *
from .xdotool_actions import *
from .virtual_cursor_path import *
from .no_driver.CursorIllustration import *
from .utils import get_value_or_default, load_config
from nodriver.core.browser import CookieJar
from nodriver.core.tab import Tab
import nodriver as uc
from typing import cast

class FantomasNoDriver():
    def __init__(self,fantomas_params=None):
        self.no_driver_instance = uc
        self.fantomas_params = fantomas_params
        self.browser_options = None
        self.emulate_movement = 0
        self.show_cursor = 0
        self.user_data_dir = "/tmp/uc_tbr34hha"
        self.browser_executable_path = "/bin/google-chrome"
        self.lang = "en-US"
        self.headless = False
        self.emulate_keyboard = 0
        if self.fantomas_params:
            self.parse_fantomas_params()
        
    def __getattr__(self, name):
         return getattr(self.no_driver_instance, name)

    async def launch_browser(self):
        try:
            await self.kill_old_chrome_process()
            await asyncio.sleep(0.3)
            self.no_driver_browser_instance = await self.no_driver_instance.start(
                headless=self.headless,
                browser_executable_path=self.browser_executable_path,
                browser_args=self.browser_options,
                lang=self.lang)
        except Exception:
            #Handling cold start error in nodriver
            await self.kill_old_chrome_process()
            await asyncio.sleep(0.3)
            self.no_driver_browser_instance = await self.no_driver_instance.start(
                headless=self.headless,
                browser_executable_path=self.browser_executable_path,
                browser_args=self.browser_options,
                lang=self.lang)

        return FantomasNoDriverBrowser(self.no_driver_browser_instance, self.emulate_movement, self.show_cursor, self.emulate_keyboard)
    
    def parse_fantomas_params(self):
        self.fantomas_params = load_config(self.fantomas_params)
        self.browser_options = get_value_or_default(self.fantomas_params.get("fantomas_browser_options"), self.browser_options)
        self.emulate_movement = get_value_or_default(self.fantomas_params.get("fantomas_emulate_movement"), self.emulate_movement)
        self.show_cursor = get_value_or_default(self.fantomas_params.get("fantomas_show_cursor"), self.show_cursor)
        self.user_data_dir = get_value_or_default(self.fantomas_params.get("fantomas_user_data_dir"), self.user_data_dir)
        self.browser_executable_path = get_value_or_default(self.fantomas_params.get("fantomas_browser_executable_path"), self.browser_executable_path)
        self.lang = get_value_or_default(self.fantomas_params.get("fantomas_lang"), self.lang)
        self.headless = get_value_or_default(self.fantomas_params.get("fantomas_headless"), self.headless)
        self.emulate_keyboard = get_value_or_default(self.fantomas_params.get("fantomas_emulate_keyboard"), self.emulate_keyboard)
    
    @staticmethod
    async def kill_old_chrome_process():
        import subprocess
        # Search for processes matching "hide-crash-restore-bubble"
        process = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True
        )
        lines = [
            line for line in process.stdout.splitlines()
            if "hide-crash-restore-bubble" in line and "grep" not in line
        ]
        #Extract the PIDs (2nd element) and kill the processes
        for line in lines:
            parts = line.split()
            pid = parts[1] 
            subprocess.run(["kill", "-9", pid])
    
class FantomasNoDriverBrowser(Browser):

    def __init__(self, no_driver_browser_instance, emulate_movement, show_cursor,emulate_keyboard):
        self.no_driver_browser_instance = no_driver_browser_instance
        self.show_cursor = show_cursor
        self.emulate_movement = emulate_movement
        self.emulate_keyboard = emulate_keyboard
    
    def __getattr__(self, name):
        return getattr(self.no_driver_browser_instance, name)
    
    async def get(self, page_url):

        tab = await self.no_driver_browser_instance.get(page_url)
        return FantomasNoDriverTab(tab, self.emulate_movement, self.show_cursor,self.emulate_keyboard)

    async def open_new_tab(self,page_url):
        tab = await self.no_driver_browser_instance.get(page_url,new_tab=True)
        return FantomasNoDriverTab(tab, self.emulate_movement, self.show_cursor,self.emulate_keyboard)

    async def open_new_window(self,page_url):
        tab = await self.no_driver_browser_instance.get(page_url,new_window=True)
        return FantomasNoDriverTab(tab, self.emulate_movement, self.show_cursor,self.emulate_keyboard)

    
    async def open_and_screenshot_image_to_b64(self,image_url):
        secondary_tab = await self.open_new_tab(image_url)
        element_to_screenshot = await secondary_tab.query_selector("img")
        pos = await element_to_screenshot.get_position()
        viewport = pos.to_viewport(1)
        data = await element_to_screenshot._tab.send(
            cdp.page.capture_screenshot(
                "jpeg", clip=viewport, capture_beyond_viewport=True
            )
        )
        await secondary_tab.close()
        return data
    
    #MonkeyPatching cookie injection
    @property
    def cookies(self):
        if not self._cookies:
            self._cookies = CookieJarMonkey(self)
        return self._cookies



class CookieJarMonkey(CookieJar):
    @staticmethod
    def _to_cookie_params(cookies):
        params = []
        for cookie in cookies:
            if isinstance(cookie, dict):
                params.append(cdp.network.CookieParam(**cookie))
            else:
                params.append(cookie)
        return params

    async def set_all(self, cookies):
        cookies = self._to_cookie_params(cookies)
        connection = None
        for tab in self._browser.tabs:
            if tab.closed:
                continue
            connection = tab
            break
        else:
            connection = self._browser.connection
        await connection.send(cdp.storage.set_cookies(cookies))


class FantomasNoDriverTab(Tab):

    def __init__(self,
                 no_driver_tab_instance: Tab, 
                 emulate_movement: int, 
                 show_cursor: int,
                 emulate_keyboard: int):
        self.no_driver_tab_instance = no_driver_tab_instance
        self.emulate_movement = emulate_movement
        self.show_cursor = show_cursor
        self.emulate_keyboard = emulate_keyboard
        self.cursor_position = [0,0]
    
    def __getattr__(self, 
                    name: str):
        return getattr(self.no_driver_tab_instance, name)
    
    def __dir__(self):
        return list(set(
            dir(type(self)) +  # attributs de la classe actuelle
            dir(self) +        # attributs de l’instance
            dir(Tab)     # attributs de l'objet "parent"
        ))
    
    async def xclick_native(self,selector_list: list,
                            sleep_list: list,
                            proportion_list: list=[0.5,0.5]):
        css_selector,css_selector_index = selector_list
        sleep_before, sleep_after = sleep_list
        await self.no_driver_tab_instance.wait_for(selector=css_selector) 

        if self.emulate_movement:
            x,y,width,height = await get_coordinates_and_size(self,selector_list)
            if proportion_list:
                x = x + proportion_list[0]*width
                y = y + proportion_list[1]*height
            viewport_width, viewport_height = await get_viewport_size(self)
            self.cursor_position = await self.xmove_native(selector_list)

        await self.xsleep(sleep_before) 
        elements = await self.no_driver_tab_instance.select_all(css_selector)
        element = elements[css_selector_index]
        await element.click()
        await self.xsleep(sleep_after)
    
    async def xsend_native(self,
                           selector_list: list,
                           sleep_list: list,text=None):
        css_selector,css_selector_index = selector_list
        sleep_before,sleep_after = sleep_list
        await self.no_driver_tab_instance.wait_for(selector=css_selector)
        await self.xsleep(sleep_before)
        targetted_elements = await self.select_all(css_selector)
        targetted_element = targetted_elements[css_selector_index]
        await self.xclick_native(selector_list,[0,0])
        if self.emulate_keyboard:
            await self._fill_native(targetted_element,text)
        else:
            await targetted_element.send_keys(text)
        await self.xsleep(sleep_after)
    
    async def xmove_native(self, 
                           selector_list: list):
        x,y,width,height = await get_coordinates_and_size(self,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        path = VirtualCursorPath().get_virtual_cursor_path(self.cursor_position,[x,y],viewport_width,viewport_height)
        if self.show_cursor:
            await cursor_illustration_show_native(self)
        for i in range(len(path[0])):
            await self.send(cdp.input_.dispatch_mouse_event("mouseMoved",path[0][i],path[1][i]))
        if self.show_cursor:
            await cursor_illustration_delete_native(self)
        self.cursor_position = [x,y]
        return [x,y]
    
    
    async def xsleep(self, 
                     sleeping_time: int, 
                     factor:int=None):
        if sleeping_time == 0:
            randomized_sleeping_time = 0 
        elif sleeping_time == 0.5:
            randomized_sleeping_time = random.uniform(0.15, 0.6)    
        else:
            randomized_sleeping_time = random.uniform(sleeping_time-0.5, sleeping_time+0.5)
        await self.no_driver_tab_instance.sleep(randomized_sleeping_time)
    
    async def xwaiter(self,
                      css_selector: str,
                      timeout_delay: int,
                      sleep_list: list):
        sleep_before,sleep_after = sleep_list
        await self.xsleep(sleep_before)
        await self.wait_for(selector=css_selector, timeout=timeout_delay)
        await self.xsleep(sleep_after)

    async def xdetector(self,
                        css_selector: str,
                        sleep_list: list):
        sleep_before, sleep_after = sleep_list
        await self.xsleep(sleep_before)
        try:
            css_selector_list = await self.select_all(css_selector, timeout=10)
            await self.xsleep(sleep_after)
            return bool(css_selector_list)
        except Exception:
            return False
        
    async def xscrape_attribute_in_iframe(self, 
                                          iframe_number: int, 
                                          selector_list: list,
                                          targetted_attribute: str):
        css_selector,ordinal = selector_list #Parsing
        full_document = await self.send(cdp.dom.get_document(-1, True))
        iframes_list = get_iframes_of_document(full_document)
        iframe = iframes_list[iframe_number]
        iframe_node_id = iframe.node_id
        targetted_elements_array = await self.send(cdp.dom.query_selector_all(iframe_node_id,css_selector))
        targetted_element_node_id = targetted_elements_array[ordinal]
        targetted_element_attributes = await self.send(cdp.dom.get_attributes(targetted_element_node_id))
        index =  targetted_element_attributes.index(targetted_attribute)
        return targetted_element_attributes[index + 1]
    
    async def xscrape_html_in_iframe(self,
                                     iframe_number: int,
                                     selector_list: list):
        css_selector,ordinal = selector_list
        full_document = await self.send(cdp.dom.get_document(-1, True))
        iframes_list = get_iframes_of_document(full_document)
        iframe = iframes_list[iframe_number]
        iframe_node_id = iframe.node_id
        targetted_elements_list = await self.send(cdp.dom.query_selector_all(iframe_node_id,css_selector))
        targetted_element_node_id = targetted_elements_list[ordinal]
        outer_html = await self.send(cdp.dom.get_outer_html(targetted_element_node_id))
        return outer_html
    
    async def xtemporary_zoom(self,
                              value_zoom: int):
        command = "document.body.style.zoom="+str(value_zoom)
        await self.send(cdp.runtime.evaluate(command))
        await self.send(cdp.runtime.disable())
    
    async def xinject_js(self,
                         js_command: str):
           js_output = await self.send(cdp.runtime.evaluate(js_command,
                                                        return_by_value=True,allow_unsafe_eval_blocked_by_csp=True))     
           return js_output 
    
    async def xupload_file(self,
                           selector_list: list,
                           file_path: str):
        css_selector,ordinal = selector_list
        doc = await self.send(cdp.dom.get_document(-1, True))
        page_node = doc.node_id
        targetted_elements_list = await self.send(cdp.dom.query_selector_all(page_node,css_selector))
        element = targetted_elements_list[ordinal]
        await self.send(cdp.dom.set_file_input_files([file_path],element))

        
    async def _fill_native(self, element,texte: str=None):
        interval_min = random.uniform(0.01, 0.09)
        interval_max = random.uniform(0.1, 0.7)
        for i in texte:
            sleeping_delay = random.uniform(interval_min, interval_max)
            await self.xsleep(sleeping_delay)
            await element.send_keys(i)

    async def xselect_native(self,
                             selector_list: list,
                             sleep_list: list,
                             option_value: str = None,
                             option_text: str = None,
                             option_index: int = None):
        css_selector, css_selector_index = selector_list
        sleep_before, sleep_after = sleep_list
        await self.no_driver_tab_instance.wait_for(selector=css_selector)

        if self.emulate_movement:
            self.cursor_position = await self.xmove_native(selector_list)

        await self.xsleep(sleep_before)

        doc = await self.send(cdp.dom.get_document(-1, True))
        page_node_id = doc.node_id
        select_elements = await self.send(cdp.dom.query_selector_all(page_node_id, css_selector))
        select_node_id = select_elements[css_selector_index]

        option_elements = await self.send(cdp.dom.query_selector_all(select_node_id, "option"))

        target_option_node_id = None

        if option_index is not None:
            target_option_node_id = option_elements[option_index]
        elif option_value is not None:
            for option_node_id in option_elements:
                attributes = await self.send(cdp.dom.get_attributes(option_node_id))
                if "value" in attributes:
                    value_index = attributes.index("value")
                    if attributes[value_index + 1] == option_value:
                        target_option_node_id = option_node_id
                        break
        elif option_text is not None:
            for option_node_id in option_elements:
                outer_html = await self.send(cdp.dom.get_outer_html(option_node_id))
                import re
                text_match = re.search(r'>([^<]*)<', outer_html)
                if text_match and text_match.group(1).strip() == option_text:
                    target_option_node_id = option_node_id
                    break
        else:
            raise ValueError("Must provide one of: option_value, option_text, or option_index")

        if target_option_node_id:
            await self.send(cdp.dom.set_attribute_value(target_option_node_id, "selected", "selected"))
            await self.send(cdp.dom.focus(select_node_id))

        await self.xsleep(sleep_after)

#==================================================================#
#                            XDO METHODS
#==================================================================#

    async def xclick_xdo(self,
                         selector_list: list,
                         sleep_list: list,
                         proportion_list: list=[0.5,0.5]):
        css_selector,ordinal = selector_list 
        await self.no_driver_tab_instance.wait_for(selector=css_selector) 
        x,y, width,height = await get_coordinates_and_size(self,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        self.cursor_position = XdoToolActions(self.show_cursor, self.emulate_movement).xclick_xdo(self.cursor_position,x,y,width,height,viewport_width,viewport_height,sleep_list,proportion_list)

    async def xclick_iframe_xdo(self, 
                                iframe_number: int,
                                selector_list: list,
                                sleep_list: list,
                                proportion_list: list=[0.5,0.5]):
        x,y,width,height = await get_coordinates_and_size_in_iframe(self,iframe_number,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        self.cursor_position = XdoToolActions(self.show_cursor, self.emulate_movement).xclick_xdo(self.cursor_position,x,y,width,height,viewport_width,viewport_height,sleep_list,proportion_list)

    async def xsend_xdo(self,
                        selector_list: list,
                        sleep_list: list,
                        text: str=None,
                        proportion_list: list=[0.5,0.5]):
        css_selector,ordinal = selector_list
        await self.no_driver_tab_instance.wait_for(selector=css_selector) 
        x,y, width,height = await get_coordinates_and_size(self,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        self.cursor_position = XdoToolActions(self.show_cursor, self.emulate_movement).xsend_xdo(self.cursor_position,x,y,width,height,viewport_width,viewport_height,sleep_list,text,proportion_list)
    
    async def xsend_iframe_xdo(self, iframe_number: int, selector_list: list,sleep_list: list,text=None, proportion_list: list=[0.5,0.5]):
        x,y,width,height = await get_coordinates_and_size_in_iframe(self,iframe_number,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        self.cursor_position = XdoToolActions(self.show_cursor, self.emulate_movement).xsend_xdo(self.cursor_position,x,y,width,height,viewport_width,viewport_height,sleep_list,text,proportion_list)

    async def xmove_xdo(self,selector_list: list):
        x,y,width,height = await get_coordinates_and_size(self,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        self.cursor_position = XdoToolActions(self.show_cursor, self.emulate_movement).xmove_xdo(self.cursor_position,x,y,viewport_width,viewport_height)
    
    async def xmove_xdo_iframe(self,selector_list: list,iframe_number: int):
        x,y,width,height = await get_coordinates_and_size_in_iframe(self,iframe_number,selector_list)
        viewport_width, viewport_height = await get_viewport_size(self)
        self.cursor_position = XdoToolActions(self.show_cursor, self.emulate_movement).xmove_xdo(self.cursor_position,x,y,viewport_width,viewport_height)