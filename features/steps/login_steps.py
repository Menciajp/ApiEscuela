from behave import given, when, then
from fastapi.testclient import TestClient
from app.main import app

# Instanciamos el cliente de pruebas globalmente para este escenario
client = TestClient(app)

@given('que tengo las credenciales de un tutor válido con usuario "{usuario}" y clave "{clave}"')
def step_dado_credenciales(context, usuario, clave):
    # Guardamos las credenciales en el "contexto" de Behave para usarlas en el siguiente paso
    context.datos_login = {
        "username": usuario,
        "password": clave
    }

@when('envío una solicitud POST a "{endpoint}" con estas credenciales')
def step_cuando_envio_solicitud(context, endpoint):
    # Ejecutamos la petición usando el TestClient de FastAPI
    context.respuesta = client.post(endpoint, data=context.datos_login)

@then('el sistema responde con un código de estado {codigo:d}')
def step_entonces_codigo_estado(context, codigo):
    # Verificamos que el status code sea el esperado (200)
    assert context.respuesta.status_code == codigo, f"Se esperaba {codigo} pero se obtuvo {context.respuesta.status_code}"

@then('la respuesta contiene un "{campo}"')
def step_entonces_contiene_campo(context, campo):
    # Verificamos que el JSON devuelto contenga el access_token
    json_respuesta = context.respuesta.json()
    assert campo in json_respuesta, f"El campo {campo} no está en la respuesta"

@then('el rol asignado en la respuesta es "{rol_esperado}"')
def step_entonces_rol_asignado(context, rol_esperado):
    # Verificamos que el rol devuelto sea el correcto
    json_respuesta = context.respuesta.json()
    assert json_respuesta.get("rol") == rol_esperado, f"Se esperaba el rol {rol_esperado}"