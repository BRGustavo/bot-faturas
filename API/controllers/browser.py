from playwright.async_api import async_playwright, TimeoutError
import zipfile
import os
from datetime import date

class BrowserAutomation:
    def __init__(self):
        self.__play_wright = None
        self.browser = None
        self.context = None
        self.page = None
        

    async def __aenter__(self, *args, **kwargs):
        await self.__start_process_browser(*args, **kwargs)
        return self

    async def __aexit__(self, exec_type, exc, tb):
        await self.close()

    async def close(self):
        await self.page.close()
        await self.context.close()
        await self.browser.close()

    @staticmethod
    def wait_for_all_load(func):
        async def wrapper(self, *args, **kwargs):
            await self.page.wait_for_load_state("load")
            await func(self, *args, **kwargs)
            await self.page.wait_for_load_state("load")
        return wrapper

    @wait_for_all_load
    async def navigate_url(self, url:str):
        try:
            await self.page.goto(url)
        except TimeoutError:
            new_page_try = await self.context.new_page()
            await self.page.close()
            self.page = new_page_try
            await self.page.goto(url)

    async def __start_process_browser(self, url:str=None, head_less:bool=True):
        self.__play_wright = await async_playwright().start()
        self.browser = await self.__play_wright.chromium.launch(headless=head_less)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        if url:
            await self.navigate_url(url)

    @wait_for_all_load
    async def click_in_button(self, button_name, wait_timeout=30, double_click=False):
        if isinstance(button_name, str):
            selector_button = await self.page.wait_for_selector(button_name, timeout=wait_timeout*1000)
        else:
            selector_button = button_name

        if double_click:
            await selector_button.dblclick()
        else:
            await selector_button.click()

    @wait_for_all_load
    async def element_is_visible(self, selector:str, wait_time:int=30):
        return_value = False
        try:
            await self.page.wait_for_selector(selector, timeout=wait_time*1000)
            return_value = True
        except TimeoutError:
            pass

        return return_value

    @wait_for_all_load
    async def fill_input(self, input_name, value, wait_visible=True, wait_timeout=30, delay=0):
        selector_input = await self.page.wait_for_selector(input_name, state="visible", timeout=wait_timeout*1000)
        
        if wait_timeout >= 1:
            await selector_input.type(value, delay=delay)
        else:
            await selector_input.fill(value)

    
    @wait_for_all_load
    async def wait_timeout(self, timeout=30):
        await self.page.wait_for_timeout(timeout*1000)
        
    async def get_current_date(self):
        get_today_date = date.today()
        current_month = get_today_date.strftime("%m")
        current_year = get_today_date.strftime("%Y")
        return (current_month, current_year)
    
    @wait_for_all_load
    async def return_element_content(self, selector, children="", wait_timeout=30):
        if isinstance(selector, str):
            element_selector = await self.page.wait_for_selector(selector, timeout=wait_timeout*1000)
            return await element_selector.inner_text()
        else:
            element_selector = await selector.wait_for_selector(children, timeout=wait_timeout*1000)
    
            return await element_selector.inner_text()
            
    
    @wait_for_all_load
    async def list_all_element_childrens(self, element, children_selector, wait_timeout=30):
        if isinstance(element, str):
            element = await self.page.wait_for_selector(element, timeout=wait_timeout*1000)
            return await element.query_selector_all(children_selector)
        else:
            return await element.query_selector_all(children_selector)

    async def extract_files(self, folder, filename):
        # Extraindo arquivos
        file_item = zipfile.ZipFile(f"{folder}{filename}.zip")
        file_item.extractall(f"{folder}Folder_{filename}")
        file_item.close()

        # Removendo arquivos anteriores
        if os.path.isfile(f"{folder}{filename}.zip"):
            os.remove(f"{folder}{filename}.zip")

    async def get_url(self):
        return self.page.url