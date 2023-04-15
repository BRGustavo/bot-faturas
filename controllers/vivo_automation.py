from .browser import BrowserService
from playwright.async_api import async_playwright, TimeoutError
import uuid
import os


async def vivo_main(credentials):
    async with async_playwright() as playwright:
        browser = BrowserService(playwright)
        await browser.start()

        # Vai até a página da vivo
        await browser.navigate("https://www.vivo.com.br/para-empresas")
        await browser.page.type("[id='compassCity']", "Arapoti")
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
        await browser.page.wait_for_timeout(1*1000)
        await browser.page.type('[type="password"]', credentials[0]['password'].strip(), delay=100)
        await browser.click_in_button("[type='submit']")

        await browser.page.wait_for_selector("[class='subtitle']", timeout=50*1000)
        await browser.page.hover("[class='subtitle']", timeout=50*1000)

        # Verificando Downloads
        find_another_invoice = False

        try:
            if find_another_invoice:
                # Caso encontre o menu lateral roxo com os "Downloads"
                toats_box = await browser.page.wait_for_selector("[class='dialog']")
                try:
                    await toats_box.wait_for_selector("[class='toggle-dialog dialog-icon closed']", timeout=2*1000)
                    await toats_box.click("[class='toggle-dialog dialog-icon closed']")

                except TimeoutError:
                    # Caso o menu roxo não esteja fechado.
                    raise TimeoutError("Não encontrou a fatura detalhada")
                finally:
                    # Avaliando se há uma "Conta detalhada" já baixada nas últimas 24hrs.
                    try:
                        await toats_box.wait_for_selector("text='Conta detalhada'", timeout=2*1000)
                        print("Tem conta detalhada")
                        find_another_invoice = True

                    except TimeoutError:
                        raise TimeoutError("Não encontrou fatura detalhada.")
            else:
                raise TimeoutError("Não deu boa pae! Cancelado por hora...")
            
        except TimeoutError:
            # Caso não tenha achado a conta detalhada ou não tenha nenhum download nas últimas 24hrs.

            # Acessar Faturas
            invoice = await browser.page.wait_for_selector("text=Contas")
            await invoice.hover()

            invoice_button = await browser.page.wait_for_selector("text='Detalhes de contas e pagamentos'")
            await invoice_button.click()

            await browser.page.wait_for_load_state("load")

            download_now_button = await browser.page.wait_for_selector("text='Baixar agora'")
            await download_now_button.click()

            detail_invoice_button = await browser.page.wait_for_selector("[class='dropdown-item dropdown-button__option']")
            
            folder='./faturas/vivo/'
            # Criando pasta "Vivo" caso não exista e gerando um nome aleatório para a fatura
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            filename = uuid.uuid4()

            # Baixando fatura em PDF       
            async with browser.page.expect_download() as download_info:
                # Aguardando evento de Download iniciar
                await detail_invoice_button.click()

            download = await download_info.value
            await download.save_as(f"{folder}{filename}.pdf")
            return f"{filename}.pdf baixado com sucesso"
    
    return "Ocorreu um problema ao executar"



