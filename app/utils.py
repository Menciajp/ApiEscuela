import hashlib
import hmac
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Passlib para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_PEPPER = os.getenv("SECRET_PEPPER", "SkibidiDou")

def hash_password(password: str) -> str:
    # 1. Combinar contraseña con Pepper
    peppered = password + SECRET_PEPPER
    
    # 2. Pre-hashear con SHA-256 para evitar el límite de 72 bytes de Bcrypt
    # Esto genera una cadena de longitud fija (64 caracteres hexadecimales)
    hasher = hashlib.sha256()
    hasher.update(peppered.encode('utf-8'))
    password_hash_ready = hasher.hexdigest()
    
    # 3. Hashear con Bcrypt (Salt incluido automáticamente)
    return pwd_context.hash(password_hash_ready)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Debemos aplicar el mismo pre-hash para comparar
    peppered = plain_password + SECRET_PEPPER
    hasher = hashlib.sha256()
    hasher.update(peppered.encode('utf-8'))
    password_hash_ready = hasher.hexdigest()
    
    return pwd_context.verify(password_hash_ready, hashed_password)