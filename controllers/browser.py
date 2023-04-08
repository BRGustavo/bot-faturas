class BrowserService:
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def close(self):
        await self.browser.close()

    async def navigate(self, url:str="https://www.google.com"):
        await self.page.goto(url)
        await self.page.wait_for_load_state("load")

    async def fill_input(self, input_name, value, wait_visible=True):
        await self.page.wait_for_load_state("load")
        await self.page.wait_for_selector(input_name, state="visible")
        await self.page.fill(input_name, value)

    async def click_in_button(self, button_name, double_click=False):
        await self.page.wait_for_load_state("load")
        await self.page.wait_for_selector(button_name, state="visible")
        await self.page.click(button_name)
        await self.page.wait_for_load_state("load")
    