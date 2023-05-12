import re
import asyncio
from controllers.password import PasswordMananger
from controllers.scrapping import GenericInvoicePanel, NetSulInvoicePanel, VivoInvoicePanel, MhnetInvoicePanel
from controllers.scrapping.embratel_panel import embratel_main
from fastapi import FastAPI
from models.password import PasswordModal
from controllers.others.vivo_rateio import ApportionmentVivo

from controllers.others import FluidNow
import uvicorn

app = FastAPI(
    title="API Sistema de Faturas",
    description="""
    API que integra automações de captura de faturas nos paineis dos diversos fornecedores de internet e realiza demais serviços voltados
    ao dia a dia do setor de infraestrutura.
    """,
    version="1.0.0",
    contact={
        "nome": "Gustavo de Oliveira",
        'linkedin': "https://www.linkedin.com/in/gugusoliveira/"
    },
    docs_url="/"
)

@app.get("/credentials/", tags=['Credênciais'], summary=['Consultando credênciais de login.'])
async def get_passwords():
    global passwords
    passwords = PasswordMananger()
    senhas = passwords.credentials
    return {"response":senhas}

@app.post("/credentials/", tags=['Credênciais'], summary="Salvando uma credêncial de login.")
async def post_passwords(password:PasswordModal):
    global passwords

    passwords.credentials[password.provedor].append({
        'user': password.user,
        'password': password.password,
        'cidade': password.cidade
    })

    passwords.save()

    return {'response': password}

@app.get("/invoices/zaaz/", tags=['Download de Faturas'], summary="Iniciando robô de scrapping ZaaZ.")
async def zaaz_connect():
    result_scrapping = ""
    url = "https://sistema.zaaztelecom.com.br/central_assinante_web/login"
    async with GenericInvoicePanel(url, passwords.credentials['zaaz']) as zaaz_panel:
        result_scrapping = await zaaz_panel.execute_in_all_panel()
    return {"response": result_scrapping}

@app.get("/invoices/netsul/", tags=['Download de Faturas'], summary="Iniciando robô de scrapping NetSul.")
async def netsul_connect():
    result_scrapping = ""
    url = "https://ixc.netinfobrasil.com.br/central_assinante_web/login"
    async with NetSulInvoicePanel(url, passwords.credentials['netsul']) as zaaz_panel:
        result_scrapping = await zaaz_panel.execute_in_all_panel()
    return {"response": result_scrapping}

@app.get("/invoices/vivo/", tags=['Download de Faturas'], summary="Iniciando robô de scrapping Vivo.")
async def vivo_connect():
    return_msg = {"status": 500,"message": "Ocorreu um erro interno no servidor" }
    try:
        async with VivoInvoicePanel(passwords.credentials['vivo']) as vivo_panel:
            await vivo_panel.login()
            await vivo_panel.navigate_to_invoice()
            
    except PermissionError as error:
        return_msg = {
            'status': 401,
            'message': str(error)
        }
    return return_msg

@app.get("/invoices/mhnet/", tags=['Download de Faturas'], summary="Iniciando robô de scrapping MhNet.")
async def mhnet_connect():
    return_msg = {"status": 500,"message": "Ocorreu um erro interno no servidor" }
    try:
        async with MhnetInvoicePanel(passwords.credentials['mhnet']) as mhnet_automation:
            await mhnet_automation.execute_in_all_panel()
 
    except PermissionError as error:
        return_msg = {
            'status': 401,
            'message': str(error)
        }
    return return_msg

@app.get("/invoices/embratel/", tags=['Download de Faturas'], summary="Iniciando robô de scrapping Embratel.")
async def embratel_connect():
    return_msg = await embratel_main(passwords.credentials['embratel'])
    return {"message":return_msg}


@app.get("/apportionment/fluid/process/{id_process}", tags=['Gestão Paineis'], summary="Acessa o Painel do fluid")
async def fluid_panel_get_process(id_process:str):
    return_msg = {"status": 500,"message": "Ocorreu um erro interno no servidor" }
    process_list = id_process.split(',')
    try:
        async with FluidNow(passwords.credentials['fdn']) as fluid_panel:
            await fluid_panel.login()
            return_msg['status'] = 200
            return_msg['message'] = await fluid_panel.find_process(process_list)
            
    except PermissionError as error:
        return_msg = {
            'status': 401,
            'message': str(error)
        }

    return return_msg
    

if __name__ == "__main__":


    #Carregando senhas
    passwords = PasswordMananger()
    uvicorn.run(app, host="0.0.0.0", port=8000)

