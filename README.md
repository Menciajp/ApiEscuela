# API Escuela - Sistema de Gestión Académica

Este proyecto es una API REST  desarrollada como **Trabajo Final Integrador (TIF)**. Permite la gestión integral de una institución educativa, incluyendo asistencias, alumnos, tutores y cursos.

## ✨ Características principales
* **Autenticación Segura:** Implementación de JWT (JSON Web Tokens) para proteger rutas.
* **Gestión de Usuarios:** CRUD completo de alumnos, tutores y personal administrativo.
* **Control de Asistencias:** Registro y consulta de presentismo por curso y alumno.
* **Arquitectura:** Separación de responsabilidades mediante Routers, Schemas y Modelos.

## 🚀 Tecnologías utilizadas
* [Python 3.12+](https://www.python.org/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
* [PostgreSQL](https://www.postgresql.org/)
* [Pydantic](https://docs.pydantic.dev/) (Validación de datos)

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone [https://github.com/Menciajp/ApiEscuela.git](https://github.com/Menciajp/ApiEscuela.git)
cd ApiEscuela
```
### 2. Configurar entorno virtual
```bash
python -m venv .venv
# Activar en Windows:
.venv\Scripts\activate
# Activar en Linux/Mac:
source .venv/bin/activate
```
### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```
### 4. Variables de Entorno
Copia el archivo .env.example a uno nuevo llamado .env y completa tus datos reales:
```bash
cp .env.example .env
```
### 🖥️ Ejecución

Para iniciar el servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

### 📖 Documentación
Una vez corriendo el servidor, puedes acceder a la documentación interactiva:

    Swagger UI: http://127.0.0.1:8000/docs

    Redoc: http://127.0.0.1:8000/redoc