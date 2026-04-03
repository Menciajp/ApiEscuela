from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str  # <--- Aquí incluimos el rol (SUDO, ADMIN, TUTOR)

    class Config:
        from_attributes = True