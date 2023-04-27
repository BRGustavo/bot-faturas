from ..browser import BrowserService
from playwright.async_api import async_playwright, TimeoutError
import os

async def fluid_access_panel(credentials=None):
    async with async_playwright() as playwright:
        browser = BrowserService(playwright)
        await browser.start()
        await browser.navigate("https://0753.fluid.prd.sicredi.cloud/usuario")
        await browser.page.wait_for_load_state("load")

        try:

            button_user = await browser.page.wait_for_selector("[class='button is-link open-id-consent-btn']")
            await button_user.click()

            await browser.page.wait_for_load_state("load")
            
            # Preenchendo usuário
            field_username = await browser.page.wait_for_selector("[id='fieldUser']")
            await field_username.fill(credentials[0]['user'])

            # Preenchendo Senha
            field_password = await browser.page.wait_for_selector("[id='fieldPassword']")

            await field_password.type(credentials[0]['password'], delay=100)

            # Clicando para realizar o Login
            await browser.click_in_button("[id='btnSubmit']")

            await browser.page.wait_for_load_state("load")

            await browser.page.wait_for_timeout(5*1000)

            # Se chegar no menu principal do fluid, tenta localizar o botã processos.
            await browser.page.wait_for_selector("[class='has-text-white css-uvy3uofalse']", timeout=10*1000)

            # Navega até a área para pesquisar processos.
            await browser.navigate("https://0753.fluid.prd.sicredi.cloud/processos/processo/pesquisar")
            await browser.page.wait_for_load_state("load")

            await browser.page.wait_for_timeout(50*1000)            
        except TimeoutError:
            pass

    return "None"