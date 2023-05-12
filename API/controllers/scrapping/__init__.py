from playwright.async_api import async_playwright, TimeoutError, JSHandle
from ..browser import BrowserAutomation
from datetime import date
import base64
import uuid
import os


class GenericInvoicePanel(BrowserAutomation):
    def __init__(self, url:str, credentials:list=[]):
        self.ignore_data = False # Caso esteja como "True" baixará as faturas de outros meses.
        self.url = url
        self.logged_in = False
        self.credentials = credentials
        self.scrapping_return = []
        self.current_in_loop = 0
        
        super().__init__
    
    @staticmethod
    def wait_for_domcontent_load(func):
        async def wrapper(self, *args, **kwargs):
            await self.page.wait_for_timeout(1*500)
            await self.page.wait_for_load_state("domcontentloaded")
            await func(self, *args, **kwargs)
            await self.page.wait_for_load_state("domcontentloaded")
        return wrapper
    

    async def login(self, user:str, password:str):
        await self.navigate_url(self.url)
        await self.fill_input("[class='login']", user)
        await self.fill_input("[type='password']", password, delay=100)
        await self.click_in_button("[class='btn btn-info btn-login is-full']")
        try:
            # Verifica se apareceu a mensagem dizendo que não foi possivel logar
            await self.page.wait_for_selector("[class='iziToast-body']", timeout=3*1000)
            raise PermissionError("Não foi possivel realizar o login.")
        except TimeoutError:
            try:
                await self.page.wait_for_selector("[id='pg_fatura']", timeout=4*1000)
                self.logged_in = True
            except TimeoutError:
                raise PermissionError("Não foi possivel realizar o login.")

    async def logout(self):
        await self.click_in_button('[class="material-icons"]')
        await self.click_in_button('text=Sair')
    
    @wait_for_domcontent_load
    async def navigate_to_invoices(self):
        if self.logged_in:
            await self.click_in_button("[id='pg_fatura']")
            menu_invoice = await self.page.wait_for_selector("[class='faturas page col-md-12 animated slideInUp']")
            
            list_of_cards = await menu_invoice.query_selector_all("[class='card']")
            if list_of_cards:
                try:
                    # Tenta realizar o scrapping
                    for element_item in list_of_cards:
                        await self.list_card_invoice(element_item)
                except NameError:
                    # Caso ocorra o bug misterioso.
                    await self.click_in_button('[id="pg_home"]')
                    await self.navigate_to_invoices()
        else:
            raise PermissionError("Não foi possivel realizar o login.")
    
    @wait_for_domcontent_load
    async def list_card_invoice(self, element:JSHandle):
        try:
            await self.wait_timeout(2)
            await self.page.wait_for_load_state("load")
            await self.page.wait_for_load_state("domcontentloaded")
    
            click_to_expand = await element.wait_for_selector("[class='button_card']", timeout=3*1000)
            await self.click_in_button(click_to_expand)

            await self.page.wait_for_load_state("domcontentloaded")

            list_invoice = await element.query_selector_all("tbody > tr")

            if list_invoice:
                for invoice in list_invoice:
                    result_invoices_scrapping = await self.download_individual_invoice(invoice)
                    self.scrapping_return.append(result_invoices_scrapping)

        except TimeoutError:
            try:
                # Valida se está tudo em dia mesmo.
                invoices_ok = await element.wait_for_selector("[class='faturas_em_dia']", timeout=3*1000)
                if invoices_ok:
                    self.scrapping_return.append({
                        
                        "status": "A Fatura está em dia!",
                        "CNPJ": self.credentials[self.current_in_loop]['user'],
                        'cidade': self.credentials[self.current_in_loop]['cidade'],
                        "baixado": "Não"
                        })

            except TimeoutError:
                raise NameError("Não conseguiu localizar o item")
    
    async def download_individual_invoice(self, element:JSHandle):
        
        # Capturando o preço da fatura
        value_price = await element.wait_for_selector('[data-th="Valor até o vencimento:"]')
        value_price = await value_price.inner_text()

        # Capturando vencimento
        invoice_date = await element.wait_for_selector('[data-th="Vencimento:"]')
        invoice_date = await invoice_date.inner_text()

        current_month, current_year = await self.get_current_date()
        
        invoice_month = invoice_date.split("/")[1]
        invoice_year = invoice_date.split("/")[2]
        file_name = str(uuid.uuid4())

        if (invoice_month <= current_month and invoice_year <= current_year) or self.ignore_data == True:
            modal = await element.query_selector('[data-th="Ações:"]')
            await self.click_in_button(modal)
            # Selecionando icone de PDF
            await self.click_in_button("[class='material-icons icones-coluna icone-fatura']")

            # Capturando o source do PDF
            pdf_element = await self.page.wait_for_selector("[class='col-md-12 scroll'] > embed")
            src = await pdf_element.get_attribute("src")

            await self.page.wait_for_load_state("domcontentloaded")
            
            decode_contet = base64.b64decode(src.split(",")[1])

            if 'zaaz' in self.url:
                # Validando se a pasta "Faturas" e "ZaaZ" existem. Caso não, cria.
                save_folder = "./faturas/zaaz/"
            else:
                save_folder = "./faturas/netsul/"

            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            
            with open(f"{save_folder}{file_name}.pdf", "wb") as f:
                f.write(decode_contet)
            
            # Fechando Modal
            await self.click_in_button("[id='modalImpressaoClose']")
        return {
            "valor": value_price, 'vencimento': invoice_date, 'arquivo': f'{file_name}.pdf',
            'baixado': 'Sim' if self.ignore_data else "Não", 
            "CNPJ": self.credentials[self.current_in_loop]['user'],
            'cidade': self.credentials[self.current_in_loop]['cidade']
        }
        
    async def execute_in_all_panel(self):
        return_msg = []
        for logins in self.credentials:
            self.logged_in = False
            try:
                await self.login(logins['user'], logins['password'])
                await self.navigate_to_invoices()
                await self.logout()
            except PermissionError:
                # Caso ele tente executar o login mas aconteca algum erro.
                return_msg.append({
                    'user': logins['user'],
                    "password": logins['password'],
                    "status": "Não foi possivel executar o login usando as credênciais."
                })
            self.current_in_loop += 1

        if len(self.scrapping_return) >=1:
            return self.scrapping_return
        else:
            return return_msg

class NetSulInvoicePanel(GenericInvoicePanel):
    async def login(self, user:str, password):
        await self.navigate_url(self.url)
        await self.fill_input("[class='login']", user, delay=100)
        #await self.fill_input("[type='password']", password, delay=100)

        await self.click_in_button("[class='btn btn-info btn-login is-full']")
        try:
            # Verifica se apareceu a mensagem dizendo que não foi possivel logar
            await self.page.wait_for_selector("[class='iziToast-body']", timeout=3*1000)
            raise PermissionError("Não foi possivel realizar o login.")
        except TimeoutError:
            try:
                await self.page.wait_for_selector("[id='pg_fatura']", timeout=4*1000)
                self.logged_in = True
            except TimeoutError:
                raise PermissionError("Não foi possivel realizar o login.")

class VivoInvoicePanel(BrowserAutomation):
    def __init__(self, credentials:list):
        self.credentials = credentials

        super().__init__
    
    async def login(self):
        # Preenchendo cidade
        await self.navigate_url("https://www.vivo.com.br/para-empresas")
        await self.fill_input("[id='compassCity']", "Arapoti", delay=100)
        await self.click_in_button("[class='search__results__list'] > li", wait_timeout=50)

        await self.page.wait_for_load_state("load")
        await self.click_in_button('[class="main-menu__login__user"]', wait_timeout=30)

        # Preenchendo e-mail
        await self.fill_input('[id="login-input"]', self.credentials[0]['email'], delay=100)
        await self.click_in_button("text=Continuar")

        # Preenchendo CPF
        await self.fill_input('[id="input-document-id"]', self.credentials[0]['cpf'], delay=100)
        await self.click_in_button("text=Continuar")
        
        # Preenchendo senha
        await self.fill_input('[type="password"]', self.credentials[0]['password'], delay=100)
        await self.click_in_button("[type='submit']")
        
        try:
            await self.page.wait_for_selector("[class='subtitle']", timeout=50*1000)
        except TimeoutError:
            PermissionError("Não foi possivel logar no painel")
    
    async def navigate_to_invoice(self):
        button_account = await self.page.wait_for_selector("text=Contas")
        await button_account.hover()

        await self.click_in_button("text='Detalhes de contas e pagamentos'")

        await self.click_in_button("text='Baixar agora'")
        
        folder = await self.validate_folder()
        filename = str(uuid.uuid4()).replace("-","").strip()

        await self.download_invoices(folder, filename)

    async def download_invoices(self, folder:str, filename:str):
        detail_invoice_button = await self.page.wait_for_selector("[class='dropdown-item dropdown-button__option']")
 
        async with self.page.expect_download() as download_info:
            # Aguardando evento de Download iniciar
            await detail_invoice_button.click()

        download = await download_info.value
        await download.save_as(f"{folder}{filename}.zip")

        await self.extract_files(folder, filename)

    async def validate_folder(self):
        folder='./faturas/vivo/'
        # Criando pasta "Vivo" caso não exista e gerando um nome aleatório para a fatura

        if not os.path.exists(folder):
            os.makedirs(folder)
        
        return folder

class MhnetInvoicePanel(BrowserAutomation):
    def __init__(self, credentials:list):
        self.credentials = credentials
        super().__init__()
    
    async def login(self, user, password):
        await self.navigate_url("https://portal.mhnet.com.br/auth/login")
        await self.wait_timeout(1)

        await self.fill_input("[name='username']", user, delay=100)
        await self.fill_input("[name='password']", password, delay=100)
        await self.click_in_button("[class='MuiButton-label']")

        await self.page.wait_for_load_state("load")
        try:
            find_invoice_button = await self.page.wait_for_selector('((//*[@id="root-portal-erp-react"]/div/div/main/div/div/div[2]/div[1]/div[1]/div/div[2]/button/span[1]))', timeout=50*1000)
            if find_invoice_button:
                await self.find_invoices()
            else:
                raise PermissionError("Não foi possivel localizar o menu 'Minhas Faturas'")
        except TimeoutError:
            current_url = await self.get_url()
            if current_url == "https://portal.mhnet.com.br/auth/login":
                await self.navigate_url("https://portal.mhnet.com.br/auth/login") 
                raise PermissionError("Não conseguiu realizar o login.")
            else:
                await self.login(user, password)

    async def logout(self):
        await self.navigate_url("https://portal.mhnet.com.br/portal")
        await self.click_in_button('[title="sair"]')

    async def find_invoices(self):
        await self.click_in_button('(//*[@id="root-portal-erp-react"]/div/div/main/div/div/div[2]/div[1]/div[1]/div/div[2]/button/span[1])')
        await self.wait_timeout(4)

    async def execute_in_all_panel(self):
        for login_info in self.credentials:
            await self.login(login_info['user'], login_info['password'])
            await self.logout()
            



