from .browser import BrowserService
from playwright.async_api import async_playwright, TimeoutError

async def vivo_main(credentials):
    async with async_playwright() as playwright:
        browser = BrowserService(playwright)
        await browser.start()

        # Vai até a página da vivo
        await browser.navigate("https://www.vivo.com.br/para-empresas")
        await browser.fill_input("[id='compassCity']", "Arapoti")
        await browser.page.wait_for_load_state("load")

        # Seleciona a cidade de Arapoti
        search_list = await browser.page.wait_for_selector("[class='search__results__list'] > li")
        await search_list.click()

        # Ir até a parte do login
        await browser.page.wait_for_load_state("load")
        await browser.click_in_button('[class="main-menu__login__user"]')

        # preenchendo com e-mail
        await browser.fill_input('[id="login-input"]', credentials[0]['email'])
        await browser.click_in_button("text=Continuar")

        # Preenchendo o CPF
        await browser.fill_input('[id="input-document-id"]', credentials[0]['cpf'])
        await browser.click_in_button("text=Continuar")

        # Preenchendo a Senha
        await browser.fill_input('[type="password"]', credentials[0]['password'].strip())
        await browser.page.wait_for_timeout(1*1000)
        await browser.click_in_button("[type='submit']")

        await browser.page.wait_for_selector("[class='subtitle']", timeout=50*1000)
        await browser.page.hover("[class='subtitle']", timeout=50*1000)

        # Acessar Faturas
        invoice = await browser.page.wait_for_selector("text=Contas")
        await invoice.hover()

        invoice_button = await browser.page.wait_for_selector("text='Detalhes de contas e pagamentos'")
        await invoice_button.click()

        await browser.page.wait_for_timeout(50000)

