from playwright.async_api import async_playwright, TimeoutError
from ..browser import BrowserService
from datetime import date

async def embratel_main(credentials):
    async with async_playwright() as playwright:
        browser = BrowserService(playwright)
        await browser.start()

        await browser.navigate("https://webebt01.embratel.com.br/embratelonline/")

        for embratel_login in credentials:
            # Realizando o login no painel
            await browser.fill_input("[name='login']", embratel_login['user'])
            await browser.fill_input("[name='password']", embratel_login['password'])

            await browser.page.wait_for_timeout(1*1000)
            await browser.page.keyboard.press("Enter")

            await browser.page.wait_for_load_state("load")

            # Acessando menu de faturas
            invoices = await browser.page.wait_for_selector("text='Fatura On Line'")
            await invoices.click()

            await browser.page.wait_for_load_state("load")
            
            invoices = await browser.page.wait_for_selector("text='Acessar Fatura On Line'")
            await invoices.click()

            await browser.page.wait_for_load_state("load")

            accept_risk = await browser.page.wait_for_selector("[id='proceed-button']")
            await accept_risk.click()

            await browser.page.wait_for_load_state("load")
            
            # Aguardando carregar parte de selecionar a tada 
            get_today_date = date.today()
            current_month = get_today_date.strftime("%m")
            current_year = get_today_date.strftime("%Y")
        
            list_page_month = await browser.page.wait_for_selector("[name='sMes']")
            await list_page_month.click()

            await list_page_month.select_option(f"{current_year}{current_month}")
            await list_page_month.click()
            
            # Clicando para pesquisa faturas
            await browser.click_in_button("[id='submit']")

            await browser.page.wait_for_load_state("load")

            await browser.page.wait_for_selector("[class='txtCinzaHand ddtf-processed']")
            tablet_invoices = await browser.page.query_selector("[id='tab']")

            list_of_invoices = await tablet_invoices.query_selector_all("tbody > tr")

            for item in list_of_invoices:
                await item.click()

                button_invoice = await browser.page.wait_for_selector('text=Boleto Bancário')
                
                # Esperando uma nova página abrir
                async with browser.context.expect_page() as page_info:
                    await button_invoice.click()

                new_page = await page_info.value
                await new_page.wait_for_load_state("load")
                await new_page.set_content('''
                    <script>
                        window.print = () => {};
                    </script>
                ''')

                # Manipulando nova guia que foi aberta ao clicar em PDF

                await new_page.emulate_media(media="screen")
                await new_page.pdf(path="page.pdf")

        await browser.page.wait_for_timeout(100* 1000)