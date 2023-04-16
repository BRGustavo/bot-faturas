import asyncio
from controllers.password import PasswordMananger
from controllers.scrapping.generic_panel import generic_zaaz_main
from controllers.scrapping.vivo_panel import vivo_main
from controllers.scrapping.embratel_panel import embratel_main
from fastapi import FastAPI
from models.password import PasswordModal

import uvicorn

app = FastAPI()

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
        'login_page': password.login_page
    })

    passwords.save()

    return {'response': password}

@app.get("/invoices/zaaz/", tags=['Automação de Faturas'], summary="Iniciando robô de scrapping ZaaZ.")
async def zaaz_connect():
    result_scrapping = await generic_zaaz_main(passwords.credentials['zaaz'])
    return {"response": result_scrapping}

@app.get("/invoices/netsul/", tags=['Automação de Faturas'], summary="Iniciando robô de scrapping NetSul.")
async def netsul_connect():
    result_scrapping = await generic_zaaz_main(passwords.credentials['netsul'], False)
    return {"response": result_scrapping}

@app.get("/invoices/vivo/", tags=['Automação de Faturas'], summary="Iniciando robô de scrapping Vivo.")
async def vivo_connect():
    return_msg = await vivo_main(passwords.credentials['vivo'])
    return {"message":return_msg}

@app.get("/invoices/embratel/", tags=['Automação de Faturas'], summary="Iniciando robô de scrapping Embratel.")
async def embratel_connect():
    return_msg = await embratel_main(passwords.credentials['embratel'])
    return {"message":return_msg}

if __name__ == "__main__":
    # Carregando senhas
    passwords = PasswordMananger()

    uvicorn.run(app, host="0.0.0.0", port=8000)

