from typing import Optional
from pydantic import BaseModel


class PasswordModal(BaseModel):
    provedor: str
    user: str
    password: str
    login_page: str

