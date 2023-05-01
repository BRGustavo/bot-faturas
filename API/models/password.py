from typing import Optional, List
from pydantic import BaseModel


class PasswordModal(BaseModel):
    provedor: str
    user: str
    password: str
    cidade: str

