import asyncio
from controllers.password import PasswordMananger
from controllers.zaaz_automation import zaaz_main


if __name__ == "__main__":
    # Carregando senhas
    passwords = PasswordMananger()

    asyncio.run(zaaz_main(passwords.credentials['zaaz']))