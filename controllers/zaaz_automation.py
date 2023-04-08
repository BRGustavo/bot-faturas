import asyncio
from playwright.async_api import async_playwright, TimeoutError
from .browser import BrowserService
      
async def zaaz_main(credentials):

    async with async_playwright() as playwright:
        browser = BrowserService(playwright)
        await browser.start()
        # Executando o Login
        await browser.navigate("https://sistema.zaaztelecom.com.br/central_assinante_web/login")

        for zaaz_logins in credentials:
            try:
                await browser.fill_input("[class='login']", zaaz_logins['user'])
                await browser.fill_input("[type='password']", zaaz_logins['password'])
                await browser.click_in_button("[class='btn btn-info btn-login is-full']")
                await browser.page.wait_for_load_state("load")
                
                # Mensagem de erro na senha
                try:
                    message = await browser.page.wait_for_selector("[class='iziToast-body']", timeout=3*1000)
                    if message:
                        raise ValueError("Usuário e senha incorretos")
                except TimeoutError:
                    pass

                # Navegando até as faturas
                await browser.click_in_button("[id='pg_fatura']")

                # Selecionado e dividindo todas as faturas encontradas
                await browser.page.wait_for_selector("[class='faturas page col-md-12 animated slideInUp']")
                list_itens = await browser.page.query_selector_all("[class='faturas page col-md-12 animated slideInUp'] > div")

                for item in list_itens:
                    # Loop en cada fatura
                    try:
                        await item.wait_for_selector("text=CARREGAR FATURAS", timeout=5*1000)
                        result = await item.query_selector("text=CARREGAR FATURAS")
                        await result.click()

                        # Abrindo a Modal da fatura
                        modal = await item.query_selector('[data-th="Ações:"]')
                        await modal.click()

                        await browser.page.wait_for_load_state("load")

                        # Clicando no icone do PDF
                        icon = await browser.page.wait_for_selector("[class='material-icons icones-coluna icone-fatura']")
                        await icon.click()

                        # Capturando o "source" do arquivo
                        element = await browser.page.wait_for_selector("[class='col-md-12 scroll'] > embed")
                        src = await element.get_attribute("src")

                        # Fechando Modal
                        icon_close = await browser.page.wait_for_selector("[id='modalImpressaoClose']")
                        await icon_close.click()
                        await browser.page.wait_for_load_state("load")

                    except TimeoutError:
                        em_dia = await item.wait_for_selector("[class='faturas_em_dia']")
                        if em_dia:
                            # Não possui nenhuma fatura em aberto.
                            pass
                # Encerrando a seção da conta
                await browser.page.click('[class="material-icons"]')
                await browser.page.wait_for_load_state("load")
                await browser.page.click('text=Sair')

            except ValueError:
                # Contata que o usuário e senha está errado e recarrega o site.
                await browser.navigate("https://sistema.zaaztelecom.com.br/central_assinante_web/login")
                continue
