from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Extract
from typing import List
from datetime import date

from .. import models, schemas, auth, utils
from ..database import get_db

router = APIRouter(
    prefix="/tutores",
    tags=["Actores: Tutores"]
)

@router.post("/", response_model=schemas.actores.TutorOut, status_code=status.HTTP_201_CREATED)
def crear_tutor(
    tutor: schemas.actores.TutorCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Registra un nuevo tutor en el sistema. 
    Requiere que la dirección (id_direccion) ya esté cargada.
    """
    
    # 1. Validación de Duplicados (Username y DNI)
    tutor_existente = db.query(models.actores.Tutor).filter(
        (models.actores.Tutor.nombre_usr == tutor.nombre_usr) | 
        (models.actores.Tutor.dni == tutor.dni)
    ).first()

    if tutor_existente:
        raise HTTPException(
            status_code=400, 
            detail="El nombre de usuario o el DNI ya se encuentran registrados."
        )

    # 2. Validar que la dirección existe
    direccion = db.query(models.infraestructura.Direccion).filter(
        models.infraestructura.Direccion.id_direccion == tutor.id_direccion
    ).first()
    
    if not direccion:
        raise HTTPException(
            status_code=404, 
            detail="La dirección especificada (id_direccion) no existe. Créala primero en /infraestructura."
        )

    # 3. Preparar datos y Hashear contraseña
    # Usamos la lógica de pre-hash SHA256 que definimos en utils.py
    pass_hasheada = utils.hash_password(tutor.contrasenia)
    
    # Convertimos el esquema a diccionario y reemplazamos la clave plana
    datos_tutor = tutor.model_dump(exclude={"contrasenia"})
    
    nuevo_tutor = models.actores.Tutor(
        **datos_tutor,
        contrasenia=pass_hasheada
    )

    # 4. Persistencia
    try:
        db.add(nuevo_tutor)
        db.commit()
        db.refresh(nuevo_tutor)
        return nuevo_tutor
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al crear el tutor: {str(e)}"
        )

@router.get("/tutelados", response_model=List[schemas.actores.TuteladoAsistenciaOut])
def obtener_asistencias_tutelados(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_data)
):
    """
    Extrae el tutor del token y devuelve a sus alumnos vinculados 
    junto con el historial de inasistencias del año actual.
    """
    username = current_user.get("username")
    rol = current_user.get("rol").upper()

    # 1. Verificación de Rol
    if rol != "TUTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acceso exclusivo para usuarios con rol TUTOR."
        )

    # 2. Buscar al Tutor por su nombre_usr
    tutor = db.query(models.actores.Tutor).filter(
        models.actores.Tutor.nombre_usr == username
    ).first()
    
    if not tutor:
        raise HTTPException(status_code=404, detail="No se encontró el perfil de tutor.")

    # 3. Preparar el año actual para las inasistencias
    anio_actual = date.today().year
    resultado = []

    # 4. Navegar por la tabla intermedia (alumnos_detalles)
    # tutor.alumnos_detalles es una lista de objetos 'AlumnoTutor'
    for vinculo in tutor.alumnos_detalles:
        alumno = vinculo.alumno # Aquí accedemos al objeto Alumno real

        # Buscamos las asistencias grabadas (Ausente, Tardanza, etc.) del año
        inasistencias = db.query(models.infraestructura.Asistencia).filter(
            models.infraestructura.Asistencia.id_alumno == alumno.id_alumno,
            Extract('year', models.infraestructura.Asistencia.fecha) == anio_actual
        ).order_by(models.infraestructura.Asistencia.fecha.desc()).all()

        # Armamos el objeto según el esquema TuteladoAsistenciaOut
        resultado.append({
            "id_alumno": alumno.id_alumno,
            "nombre": alumno.nombre,
            "apellido": alumno.apellido,
            "dni": alumno.dni,
            "inasistencias": inasistencias
        })

    return resultado

@router.get("/{dni}", response_model=schemas.actores.TutorOut)
def buscar_tutor_por_dni(
    dni: str,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Busca un tutor por su DNI. Solo accesible para administradores.
    """
    tutor = db.query(models.actores.Tutor).filter(
        models.actores.Tutor.dni == dni
    ).first()
    
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tutor con DNI {dni} no encontrado."
        )
    return tutor

@router.patch("/{id_tutor}", response_model=schemas.actores.TutorOut)
def modificar_tutor(
    id_tutor: int,
    tutor_data: schemas.actores.TutorUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Modifica los datos de un tutor de forma parcial.
    """
    # 1. Buscar al tutor en la base de datos
    query = db.query(models.actores.Tutor).filter(models.actores.Tutor.id_tutor == id_tutor)
    tutor_db = query.first()

    if not tutor_db:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")

    # 2. Extraer solo los campos que el usuario envió (exclude_unset=True)
    update_data = tutor_data.model_dump(exclude_unset=True)

    # 3. Lógica especial para campos sensibles o relacionales
    
    # Si se actualiza la contraseña, hay que hashearla
    if "contrasenia" in update_data:
        update_data["contrasenia"] = utils.hash_password(update_data["contrasenia"])
    
    # Si se intenta cambiar la dirección, hay que validar que el nuevo ID exista
    if "id_direccion" in update_data:
        dir_exists = db.query(models.infraestructura.Direccion).filter(
            models.infraestructura.Direccion.id_direccion == update_data["id_direccion"]
        ).first()
        if not dir_exists:
            raise HTTPException(
                status_code=404, 
                detail="La nueva dirección especificada no existe."
            )

    # 4. Aplicar los cambios
    try:
        query.update(update_data)
        db.commit()
        db.refresh(tutor_db)
        return tutor_db
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al actualizar el tutor: {str(e)}"
        )

