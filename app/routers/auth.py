from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, utils, auth, database, schemas

router = APIRouter(
    tags=["Autenticación"]
)

@router.post("/login", response_model=schemas.auth.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(database.get_db)
):
    """
    Endpoint de autenticación unificado para Empleados y Tutores.
    Retorna un Access Token (JWT) con el rol correspondiente.
    """
    
    # 1. Intentar buscar primero en la tabla de Empleados
    usuario = db.query(models.actores.Empleado).filter(
        models.actores.Empleado.nombre_usr == form_data.username
    ).first()
    
    rol_para_token = None

    if usuario:
        # Si es empleado, tomamos el rol de la BD (SUDO, ADMIN, etc.)
        rol_para_token = usuario.rol.upper()
    else:
        # 2. Si no es empleado, buscamos en la tabla de Tutores
        usuario = db.query(models.actores.Tutor).filter(
            models.actores.Tutor.nombre_usr == form_data.username
        ).first()
        
        if usuario:
            # Si es tutor, le asignamos el rol virtual "TUTOR"
            rol_para_token = "TUTOR"

    # 3. Validar si el usuario existe y si la contraseña es correcta
    # IMPORTANTE: Ambos modelos deben usar el campo 'contrasenia' 
    if not usuario or not utils.verify_password(form_data.password, usuario.contrasenia):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Crear el Token JWT con la información de identidad y rol
    access_token = auth.create_access_token(
        data={
            "sub": usuario.nombre_usr, 
            "rol": rol_para_token
        }
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "rol": rol_para_token
    }