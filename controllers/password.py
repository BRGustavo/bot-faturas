import json
import os   

class PasswordMananger:
    def __init__(self, file:str="./passwords.json"):
        self._file_path = file
        self._file_json = None
        self.__credentials = None

        self.__check_file()

    def __check_file(self):
        """
            Casse utilizada para verificar, criar carregar as informações do arquivo passwords.json
        """
        try: 
            if os.path.isfile(self._file_path):
                """
                Verifica se o arquivo existe.
                """
                pass
            else:
                """
                Caso o arquivo não exista ele retornar um erro
                """
                raise FileExistsError(f"Arquivo json de senhas não encontrado")
        except FileExistsError:
                """
                    Criando arquivo de senhas.
                """
                text = json.dumps({'zaaz':[{"user": "None", 'password':'None', "login_page":"None"}]})
                file = open(self._file_path, "a")
                file.write(text)
                file.close()
        finally:
            with open(self._file_path, "r") as file:
                self.__credentials = json.load(file) 
    
    @property
    def credentials(self):
        return self.__credentials
        