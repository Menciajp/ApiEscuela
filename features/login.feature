# language: es
Característica: Autenticación de usuarios en la API
  Como usuario del sistema
  Quiero poder iniciar sesión con mis credenciales
  Para obtener un token de acceso y mi rol correspondiente

  Escenario: Inicio de sesión exitoso de un Tutor
    Dado que tengo las credenciales de un tutor válido con usuario "menciajl" y clave "contrasenia"
    Cuando envío una solicitud POST a "/login" con estas credenciales
    Entonces el sistema responde con un código de estado 200
    Y la respuesta contiene un "access_token"
    Y el rol asignado en la respuesta es "TUTOR"