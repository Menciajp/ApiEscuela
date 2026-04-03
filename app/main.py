import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import usuarios, auth, infraestructura,tutores,alumnos,academia,cursos, asistencias  # Importamos el router recién creado

load_dotenv()
app = FastAPI(
    title="API Escuela",
    description="Sistema de gestión académica con autenticación JWT",
    version="1.0.0"
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173") 

origins = [
    FRONTEND_URL,
    "http://127.0.0.1:5173", # Agregamos variantes comunes por las dudas
]

# 3. Agregar el middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Permitir solo tu frontend
    allow_credentials=True,
    allow_methods=["*"],              # Permitir todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Permitir todos los headers (incluyendo el de Authorization para JWT)
)

# Registro de routers
app.include_router(usuarios.router)
app.include_router(auth.router)
app.include_router(infraestructura.router)  
app.include_router(tutores.router)  
app.include_router(alumnos.router) 
app.include_router(academia.router)
app.include_router(cursos.router)  
app.include_router(asistencias.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a ApiEscuela - El servidor está activo"}