import pytest
from fastapi.testclient import TestClient
from jose import jwt
from datetime import timedelta
import os
from app.main import app
#pytest test_auth.py para ejecutar
# Importamos las funciones y variables de tu archivo (asumiendo que se llama auth.py)
from app.auth import create_access_token, SECRET_KEY, ALGORITHM

#prueba unitaria
def test_create_access_token_genera_token_valido():
    # 1. Preparar los datos de prueba (Arrange)
    test_data = {"sub": "jlopez", "rol": "TUTOR"}
    test_delta = timedelta(minutes=15)

    # 2. Ejecutar la función a probar (Act)
    token = create_access_token(data=test_data, expires_delta=test_delta)

    # 3. Validar los resultados (Assert)
    # Verificamos que se haya generado un string
    assert isinstance(token, str)

    # Decodificamos el token para comprobar que la información es correcta
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert payload["sub"] == "jlopez"
    assert payload["rol"] == "TUTOR"
    assert "exp" in payload  # Verificamos que tenga fecha de expiración

#prueba de integracion 
client = TestClient(app)

def test_login_integracion_tutor_exitoso():
    """
    Prueba de integración para el circuito de login de un Tutor.
    Verifica que las credenciales correctas devuelvan un token y el rol adecuado.
    """
    # 1. Preparar los datos (Arrange)
    datos_login = {
        "username": "menciajl",
        "password": "contrasenia"
    }

    # Enviamos los datos como 'data' (form-data), que es lo que espera OAuth2PasswordRequestForm
    response = client.post("/login", data=datos_login)

    # 3. Validar los resultados (Assert)
    assert response.status_code == 200
    
    data_respuesta = response.json()
    assert "access_token" in data_respuesta
    assert data_respuesta["token_type"] == "bearer"
    assert data_respuesta["rol"] == "TUTOR"

def test_login_integracion_credenciales_invalidas():
    """
    Prueba de integración para verificar el rechazo de accesos no autorizados.
    """
    datos_login = {
        "username": "usuario_inexistente",
        "password": "clave_incorrecta"
    }

    response = client.post("/login", data=datos_login)

    # Debería devolver un error 401 Unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "Nombre de usuario o contraseña incorrectos"