import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv


# 1. URL de conexión a PostgreSQL
# Formato: postgresql://usuario:contraseña@servidor:puerto/nombre_db
load_dotenv()  # Carga las variables de entorno desde el archivo .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 2. El Engine: El responsable de la conexión física
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # El pool_size evita que la BD se sature con demasiadas conexiones abiertas
    pool_size=10, 
    max_overflow=20
)

# 3. SessionLocal: Una fábrica de "sesiones" para cada petición a la API
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Clase Base: De aquí heredarán todos nuestros modelos de tablas
class Base(DeclarativeBase):
    pass

# 5. Dependencia: Esta función nos dará una conexión limpia en cada endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()