from ..browser import BrowserAutomation
from playwright.async_api import async_playwright, TimeoutError
import os
import pandas as pd

class FluidNow(BrowserAutomation):
    
    def __init__(self, credentials:list):
        """Instância a classe responsável por realizar os processos no fluid.
        Args:
            credentials (list): 
            - Lista contendo informações de usuário e senha.
            - Ela deve ser uma lista com um dicionário contendo as chaves "user" e "password"
        """
        
        self.login_url = "https://0753.fluid.prd.sicredi.cloud/usuario"
        self.credentials = credentials
        self.logged_in = False

        super().__init__()

    async def login(self):
        """Realiza o login na plataforma fluid acessando a url e digitando as informações de login passadas como parametro para a classe.

        Raises:
            PermissionError: 
                - Ocorre quando não foi possivel chegar ao menu principal do fluid.
                - Geralmente quando o usuário ou senha está incorreto.
                - Login não permitido fora do horário definido pela plataforma.
        """
        await self.navigate_url(self.login_url)
        await self.click_in_button("[class='button is-link open-id-consent-btn']")
        await self.fill_input("[id='fieldUser']", self.credentials[0]['user'])
        await self.fill_input("[id='fieldPassword']", self.credentials[0]['password'], delay=100)
        await self.click_in_button("[id='btnSubmit']")

        success_login = await self.element_is_visible("[class='has-text-white css-uvy3uofalse']", wait_time=10)
        if success_login:
            # Valida se conseguiu encontrar o item "Processos" no menu principal do fluid
            self.logged_in = True
            pass
        else:
            await self.wait_timeout(8)
            print(self.page.url)
            now_url = ""
            if now_url == self.login_url:
                raise PermissionError("Não foi possivel realizar o login.")
            
    
    async def find_process(self, process_list:list=[]):
        process_return_list = []

        await self.navigate_url("https://0753.fluid.prd.sicredi.cloud/processos/processo/pesquisar")
        if await self.page.url() == self.login_url and self.logged_in:
            try:
                await self.login()
                await self.find_process(process_list)
                return await self.find_process(process_list)
            
            except PermissionError:
                self.logged_in = False
                raise PermissionError("Não foi possivel realizar o login novamente")
    
        for id_process in process_list:
            await self.navigate_url(f"https://0753.fluid.prd.sicredi.cloud/processos/processo/visualizar/id/{id_process}")
            instance_status = await self.return_element_content('(//*[@id="container-body"]/div[1]/div/div/div[1]/ul/li[4])')
            process_return_list.append({
                'process': str(id_process),
                'instancia': str(instance_status)
            })

        return process_return_list


async def read_excel_and_get_process():
    username = os.getenv("USERNAME")

    file = f"C:/Users/{username}/Sicredi/SUREG 0753 - Novos Horizontes - TI - TI/Controle Lançamento de Notas/" 
    return_content = [] 
    try: 
        if os.path.exists(file): 
            df = pd.read_excel(file) 
            print(df.describe()) 
        else:
            raise PermissionError("O Arquivo não existe.")
    except PermissionError: 
        return_content.append("Não foi possivel consultar processos na tabela")
        
    return [""]