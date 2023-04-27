from playwright.async_api import async_playwright, TimeoutError
from ..browser import BrowserService
from datetime import date
import base64
import uuid
import os


async def generic_zaaz_main(credentials, zaaz=True, ignore_data=False):
    """
    Objetivo do código abaixo é realizar o login no painel da ZaaZ e Netsul com o usuário e senha das agências e sede
    e capturar os boletos em aberto.
    
    Para tal, é necessário que as inforamções de usuário e senha do painel estejam atualizados no arquivo "passwords.json".

    O passso a passo seguido será:
    - Ler o arquivo de senhas;
    - Abrir o navegador chromium;
    - Acessar a URL do painel da ZaaZ e NetSul;
    - Tentar realizar o Login;
    - Navegar até as faturas;
    - Verificar se está no mês de competência;
    - Capturar o arquivo "src" (URL do boleto);
    - Enviar um request assincrôno para baixar o PDF;
    - Armazenar em uma pasta local.

    Tanto a ZaaZ quanto a NetSul usam o mesmo painel de faturas genéricos.
    """
    url = None
    if zaaz:
        url = "https://sistema.zaaztelecom.com.br/central_assinante_web/login"
    else:
        url = "https://ixc.netinfobrasil.com.br/central_assinante_web/login"

    async with async_playwright() as playwright: # Código está usando o modo assincrono
        browser = BrowserService(playwright)
        await browser.start()

        invoice_list = []

        await browser.navigate(url)

        for zaaz_logins in credentials:

            try: # Tentando fazer login com as credências fornecidas

                await browser.fill_input("[class='login']", zaaz_logins['user'])
                if zaaz:
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
                menu_invoice = await browser.page.wait_for_selector("[class='faturas page col-md-12 animated slideInUp']")
                await browser.page.wait_for_load_state("load")

                list_itens = await menu_invoice.query_selector_all("[class='card']")
                await browser.page.wait_for_load_state("load")


                async def execute_scrapping():

                    for item in list_itens:
                        result = None
                        # Loop en cada fatura
                        try:
                            await browser.page.wait_for_load_state("domcontentloaded")

                            try:
                                # Tentando achar o botão "CARREGAR FATURAS"
                                result = await item.wait_for_selector("[class='button_card']", timeout=2*1000)
                                await result.click() 
                            
                            try:
                                # Tentando achar o botão "CARREGAR FATURAS"
                                result = await item.wait_for_selector("[class='button_card']", timeout=2*1000)
                            
                            except TimeoutError:
                                # Caso não encontre pelo elemento, ele tentará pelo texto.
                                    await browser.page.wait_for_timeout(1*1000)
                                    result = await item.wait_for_selector('button', timeout=10*1000)
                            finally:
                                await result.click()
                                

                            list_invoices = await item.query_selector_all("tbody > tr")
                            
                            for invoice in list_invoices:
            
                                # Capturando o preço da fatura
                                value_price = await invoice.wait_for_selector('[data-th="Valor até o vencimento:"]')
                                value_price = await invoice.inner_text() 
                            
                                # Capturando vencimento
                                invoice_date = await invoice.wait_for_selector('[data-th="Vencimento:"]')
                                invoice_date = await invoice_date.inner_text()

                                get_today_date = date.today()
                                current_month = get_today_date.strftime("%m")
                                current_year = get_today_date.strftime("%Y")
                                
                                invoice_month = invoice_date.split("/")[1]
                                invoice_year = invoice_date.split("/")[2]

                                # Valida se está no mês de competência. 
                                # Pode ignorar a validação de data se o parâmetro "ignore_data" for passado como True.
                                if (invoice_month <= current_month and invoice_year <= current_year) or ignore_data == True:
                                    
                                    # Abrindo a Modal da fatura
                                    modal = await invoice.query_selector('[data-th="Ações:"]')
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

                                    if zaaz:
                                        # Validando se a pasta "Faturas" e "ZaaZ" existem. Caso não, cria.
                                        save_folder = "./faturas/zaaz/"
                                    else:
                                        save_folder = "./faturas/netsul/"

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

                await execute_scrapping()
                # Encerrando a seção da conta
                await browser.page.click('[class="material-icons"]')
                await browser.page.wait_for_load_state("load")
                await browser.page.click('text=Sair')

            except ValueError:
                # Contata que o usuário e senha está errado e recarrega o site.
                await browser.navigate(url)
                continue

        return invoice_list