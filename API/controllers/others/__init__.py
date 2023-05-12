from ..browser import BrowserAutomation
from playwright.async_api import async_playwright, TimeoutError
import os
import pandas as pd


class FluidProcess:
    def __init__(self, id_process:int=0, nome_autor:str=None):
        self.process_id = id_process
        self.nome_autor = nome_autor
        self.data_criacao = ""
        self.assocaido = ""
        self.instancia = ""
    
    def __str__(self) -> str:
        
        return {
            "ID": self.process_id,
            "Responsavel": self.nome_autor
            }

    async def get_process_info(self, page:BrowserAutomation):
        """Captura as informações do processo já criado.

        Args:
            page (BrowserAutomation):
            - Instância da classe utilizada para automação de navegadores.
        """
        url = await page.get_url()
        
        if self.process_id == 0:
            self.process_id = await page.return_element_content('[class="is-size-6 mr-1 has-text-info"]')
        
        self.nome_autor = await self.__line_extract_info(page, "text=Responsável", 3)
        self.data_criacao = await self.__line_extract_info(page, "text=Criação", 3)
        self.associado = await self.__line_extract_info(page, 'text=Associado', 3)
        self.instancia = await self.__line_extract_info(page, 'text=Instância', 3)
        
    async def __line_extract_info(self, page:BrowserAutomation, selector:str, max_wait=30):
        """Valida se os campos passados existem na página. Caso sim, retorna as informações.
        Args:
            page (BrowserAutomation):
            - Instância da classe utilizada para automação de navegadores.
            selector (Str):
            - Nome do campo encontrado no cabeçalho do processo.
            max_wait (int):
            - Tempo de espera para localizar o item
        """
        return_value = ""
        try:
            selector_line = await page.page.wait_for_selector(selector, timeout=max_wait*1000)

            if selector_line:
                return_value = await selector_line.wait_for_selector("xpath=..")
                return_value = await return_value.inner_text()
                return_value = self.__slice_string(return_value, ":")
        except TimeoutError:
            pass

        return return_value
    def __slice_string(self, text:str, before:str):
        """ Localiza a primeira parte do texto antes do 'before' e retora as informações posteriores.
        Args:
            text (str):
            - Texto do qual será realizado a extração das informações.
            before (str):
            - Divisor utilizado para localizar o ponto de corte da string.
        
        return --> str
        """
        find_position = text.find(before)+1
        text = text[find_position:].strip()
        if '\n' in text:
            text = text.replace("\n", '|')
        return text
    

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
        await self.fill_input("[id='fieldUser']", self.credentials[0]['selector1'])
        await self.fill_input("[id='fieldPassword']", self.credentials[0]['selector2'], delay=100)
        await self.click_in_button("[id='btnSubmit']")

        success_login = await self.element_is_visible("[class='has-text-white css-uvy3uofalse']", wait_time=10)
        if success_login:
            # Valida se conseguiu encontrar o item "Processos" no menu principal do fluid
            self.logged_in = True
            pass
        else:
            await self.wait_timeout(8)
            now_url = await self.get_url()
            if now_url == self.login_url:
                raise PermissionError("Não foi possivel realizar o login.")
            
    
    async def find_process(self, process_list:list=[]):
        process_return_list = []

        await self.navigate_url("https://0753.fluid.prd.sicredi.cloud/processos/processo/pesquisar")
        if await self.get_url() == self.login_url and self.logged_in:
            try:
                await self.login()
                await self.find_process(process_list)
                return await self.find_process(process_list)
            
            except PermissionError:
                self.logged_in = False
                raise PermissionError("Não foi possivel realizar o login novamente")
    
        for id_process in process_list:
            await self.navigate_url(f"https://0753.fluid.prd.sicredi.cloud/processos/processo/visualizar/id/{id_process}")
            await self.wait_timeout(10)

            current_process = FluidProcess(id_process)
            await current_process.get_process_info(self)

            instance_status = "None"
            process_return_list.append({
                'processo': str(id_process),
                'associado': current_process.associado,
                'responsavel': current_process.nome_autor,
                'data': current_process.data_criacao,
                'instancia': current_process.instancia
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