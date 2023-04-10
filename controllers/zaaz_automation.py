from playwright.async_api import async_playwright, TimeoutError
from .browser import BrowserService
import base64
import uuid
import os


async def zaaz_main(credentials):
    """
    Objetivo do código abaixo é realizar o login no painel da ZaaZ com o usuário e senha das agências e sede
    e capturar os boletos em aberto.
    
    Para tal, é necessário que as inforamções de usuário e senha do painel estejam atualizados no arquivo "passwords.json".

    O passso a passo seguido será:
    - Ler o arquivo de senhas;
    - Abrir o navegador chromium;
    - Acessar a URL do painel da ZaaZ;
    - Tentar realizar o Login;
    - Navegar até as faturas;
    - Capturar o arquivo "src" (URL do boleto);
    - Armazenar em uma pasta local.
    """

    async with async_playwright() as playwright: # Código está usando o modo assincrono
        browser = BrowserService(playwright)
        await browser.start()

        invoice_list = []
        # Executando o Login
        await browser.navigate("https://sistema.zaaztelecom.com.br/central_assinante_web/login")

        for zaaz_logins in credentials:

            try: # Tentando fazer login com as credências fornecidas

                await browser.fill_input("[class='login']", zaaz_logins['user'])
                await browser.fill_input("[type='password']", zaaz_logins['password'])
                await browser.click_in_button("[class='btn btn-info btn-login is-full']")
                await browser.page.wait_for_load_state("load")
                
                # Mensagem de erro na senha
                try:
                    # Valida se não aparece a mensagem de erro "Usuário e senha incorretos".
                    message = await browser.page.wait_for_selector("[class='iziToast-body']", timeout=3*1000)
                    if message:
                        # Estoura uma erro para tratamento.
                        raise ValueError("Usuário e senha incorretos")
                    
                except TimeoutError:
                    # Caso não apareça a mensagem, segue em frente.
                    pass

                # Navegando até as faturas
                await browser.click_in_button("[id='pg_fatura']")

                # Selecionado e dividindo todas as faturas encontradas
                await browser.page.wait_for_selector("[class='faturas page col-md-12 animated slideInUp']")
                list_itens = await browser.page.query_selector_all("[class='faturas page col-md-12 animated slideInUp'] > div")

                for item in list_itens:
                    # Loop en cada fatura
                    
                    try:
                        await item.wait_for_selector("[class='button_card']", timeout=5*1000)
                        result = await item.query_selector("[class='material-icons']")
                        await result.click()

                        # Capturando o preço da fatura
                        value_price = await item.wait_for_selector('[data-th="Valor até o vencimento:"]')
                        value_price = await value_price.inner_text() 
                        
                        # Capturando vencimento
                        invoice_date = await item.wait_for_selector('[data-th="Vencimento:"]')
                        invoice_date = await invoice_date.inner_text()

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

                        # Transformando URL em arquivo e definido o nome.
                        decode_contet = base64.b64decode(src.split(",")[1])
                        file_name = str(uuid.uuid4())

                        # Validando se a pasta "Faturas" e "ZaaZ" existem. Caso não, cria.
                        save_folder = "./faturas/zaaz/"
                        if not os.path.exists(save_folder):
                            os.makedirs(save_folder)

                        # Salvando o PDF na pasta
                        with open(f"{save_folder}{file_name}.pdf", "wb") as f:
                            f.write(decode_contet)

                        invoice_list.append({
                            'src': f"{file_name}.pdf",
                            'price': value_price,
                            'due date': invoice_date
                        })

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

        return invoice_list