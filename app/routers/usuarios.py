from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, utils
from ..auth import RoleChecker
from ..database import get_db

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios / Empleados"]
)

@router.post("/", response_model=schemas.actores.EmpleadoOut, status_code=status.HTTP_201_CREATED)
def crear_empleado(empleado: schemas.actores.EmpleadoCreate, db: Session = Depends(get_db), user=Depends(RoleChecker(["SUDO", "ADMIN"]))):
    # 1. Validación de Duplicados (Username y DNI)
    # Verificamos si el nombre de usuario ya existe
    usuario_existente = db.query(models.actores.Empleado).filter(
        models.actores.Empleado.nombre_usr == empleado.nombre_usr
    ).first()
    
    if usuario_existente:
        raise HTTPException(
            status_code=400, 
            detail="El nombre de usuario ya está en uso."
        )

    # Verificamos si el DNI ya existe (importante en sistemas escolares)
    dni_existente = db.query(models.actores.Empleado).filter(
        models.actores.Empleado.dni == empleado.dni
    ).first()
    
    if dni_existente:
        raise HTTPException(
            status_code=400, 
            detail="Ya existe un empleado registrado con ese DNI."
        )

    # 2. Procesamiento de Seguridad
    # Hasheamos usando el campo 'contrasenia' de tu schema
    hashed_pass = utils.hash_password(empleado.contrasenia)
    
    # 3. Mapeo de datos al Modelo SQLAlchemy
    # Extraemos los datos a un diccionario y removemos la clave plana
    datos_dict = empleado.model_dump(exclude={"contrasenia"})
    datos_dict["rol"] = datos_dict["rol"].upper()
    
    nuevo_empleado = models.actores.Empleado(
        **datos_dict, 
        contrasenia=hashed_pass # Asumiendo que en el modelo se llama hashed_password
    )

    # 4. Persistencia
    try:
        db.add(nuevo_empleado)
        db.commit()
        db.refresh(nuevo_empleado)
        return nuevo_empleado
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error en la base de datos: {str(e)}"
        )  

@router.post("/setup-sudo", status_code=status.HTTP_201_CREATED, tags=["Inicialización"])
def crear_superuser_inicial(db: Session = Depends(get_db)):
    """
    Crea el superusuario (SUDO) inicial con los requisitos mínimos de espacio.
    """
    
    # 1. Verificar si ya existe el SUDO para evitar duplicados
    sudo_exists = db.query(models.actores.Empleado).filter(
        models.actores.Empleado.nombre_usr == "superuser"
    ).first()

    if sudo_exists:
        raise HTTPException(
            status_code=400, 
            detail="El superusuario ya ha sido inicializado."
        )

    # 2. Hashear la contraseña (puedes cambiar 'sudo1234' por lo que prefieras)
    pass_hasheada = utils.hash_password("sudo1234")

    # 3. Creación minimalista
    nuevo_sudo = models.actores.Empleado(
        nombre="Sudo",
        apellido="Root",
        dni="0000",            # Mínimo espacio
        nombre_usr="superuser", # Tu 'login' de superusuario
        rol="SUDO",            # Rol jerárquico máximo
        contrasenia=pass_hasheada,
        telefono=None          # No ocupa espacio adicional
    )

    try:
        db.add(nuevo_sudo)
        db.commit()
        db.refresh(nuevo_sudo)
        return {
            "status": "success",
            "message": "Superusuario (SUDO) creado exitosamente",
            "login": "superuser"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al crear el SUDO: {str(e)}"
        )

@router.get("/{dni}", response_model=schemas.actores.EmpleadoOut)
def buscar_empleado_por_dni(
    dni: str, 
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Busca un empleado específico en la base de datos usando su DNI.
    Restringido a roles SUDO y ADMIN.
    """
    
    # 1. Realizar la búsqueda en PostgreSQL
    # Buscamos en la tabla de empleados filtrando por la columna 'dni'
    empleado = db.query(models.actores.Empleado).filter(
        models.actores.Empleado.dni == dni
    ).first()

    # 2. Validar si el empleado existe
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún empleado con el DNI: {dni}"
        )

    # 3. Retornar el resultado
    # FastAPI se encarga de convertir el modelo SQLAlchemy al esquema EmpleadoOut
    return empleado    

@router.patch("/{id_empleado}", response_model=schemas.actores.EmpleadoOut)
def modificar_empleado(
    id_empleado: int,
    empleado_data: schemas.actores.EmpleadoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["SUDO", "ADMIN"]))
):
    # 1. Buscar el empleado existente
    query = db.query(models.actores.Empleado).filter(models.actores.Empleado.id_empleado == id_empleado)
    empleado_db = query.first()

    if not empleado_db:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    # 2. Protección de Jerarquía
    # Un ADMIN no puede modificar a un SUDO
    if empleado_db.rol == "SUDO" and current_user["rol"] != "SUDO":
        raise HTTPException(
            status_code=403, 
            detail="No tienes permisos para modificar a un Superusuario (SUDO)."
        )

    # 3. Preparar los datos para actualizar (Pydantic v2)
    # 'exclude_unset=True' ignora los campos que el usuario no envió en el JSON
    update_data = empleado_data.model_dump(exclude_unset=True)

    # 4. Lógica especial para campos críticos
    if "contrasenia" in update_data:
        update_data["contrasenia"] = utils.hash_password(update_data["contrasenia"])
    
    if "rol" in update_data:
        # Solo SUDO puede otorgar el rango SUDO
        nuevo_rol = update_data["rol"].upper()
        if nuevo_rol == "SUDO" and current_user["rol"] != "SUDO":
            raise HTTPException(status_code=403, detail="No puedes asignar el rol SUDO.")
        update_data["rol"] = nuevo_rol

    # 5. Aplicar cambios y persistir
    query.update(update_data)
    
    try:
        db.commit()
        db.refresh(empleado_db)
        return empleado_db
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")
    
@router.get("/", response_model=List[schemas.actores.EmpleadoOut])
def listar_empleados_por_rol(
    rol: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Trae todos los empleados. Si se pasa el parámetro ?rol=, filtra por ese rol.
    """
    query = db.query(models.actores.Empleado)
    if rol:
        query = query.filter(models.actores.Empleado.rol == rol.upper())
    
    return query.all()