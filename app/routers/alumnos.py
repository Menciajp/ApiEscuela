from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/alumnos",
    tags=["Actores: Alumnos"]
)

# =================================================================
# 1. CREAR ALUMNO (POST)
# =================================================================
@router.post("/", response_model=schemas.actores.AlumnoOut, status_code=status.HTTP_201_CREATED)
def crear_alumno(
    alumno: schemas.actores.AlumnoCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    # A. Validar DNI único
    if db.query(models.actores.Alumno).filter(models.actores.Alumno.dni == alumno.dni).first():
        raise HTTPException(status_code=400, detail="El DNI del alumno ya está registrado.")

    # B. Validar Dirección
    direccion = db.query(models.infraestructura.Direccion).filter(
        models.infraestructura.Direccion.id_direccion == alumno.id_direccion
    ).first()
    if not direccion:
        raise HTTPException(status_code=404, detail="La dirección especificada no existe.")

    # C. Crear instancia del Alumno (sin los tutores aún)
    datos_alumno = alumno.model_dump(exclude={"tutores"})
    nuevo_alumno = models.actores.Alumno(**datos_alumno)
    
    db.add(nuevo_alumno)
    db.flush()  # Genera el id_alumno sin cerrar la transacción

    # D. Crear los vínculos con Tutores en la tabla intermedia
    for v in alumno.tutores:
        # Verificar que el tutor exista
        tutor_db = db.query(models.actores.Tutor).filter(models.actores.Tutor.id_tutor == v.id_tutor).first()
        if not tutor_db:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Tutor ID {v.id_tutor} no encontrado.")
        
        # Crear la fila en la tabla de asociación
        nuevo_vinculo = models.actores.AlumnoTutor(
            id_alumno=nuevo_alumno.id_alumno,
            id_tutor=v.id_tutor,
            parentesco=v.parentesco,
            es_principal=v.es_principal
        )
        db.add(nuevo_vinculo)

    try:
        db.commit()
        db.refresh(nuevo_alumno)
        return nuevo_alumno
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar: {str(e)}")

# =================================================================
# 2. BUSCAR ALUMNO (GET)
# =================================================================
@router.get("/{dni}", response_model=schemas.actores.AlumnoOut)
def buscar_alumno_por_dni(
    dni: str, 
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    # 1. Buscamos al alumno por DNI
    alumno = db.query(models.actores.Alumno).filter(models.actores.Alumno.dni == dni).first()
    
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")

    # 2. Buscamos el curso donde esté ACTIVO actualmente
    # Cruzamos con la tabla asociativa 'alumno_integra_curso'
    tabla_vinculo = models.academia.alumno_integra_curso
    
    curso_actual = db.query(models.academia.Curso).join(
        tabla_vinculo, 
        models.academia.Curso.id_curso == tabla_vinculo.c.id_curso
    ).filter(
        tabla_vinculo.c.id_alumno == alumno.id_alumno,
        tabla_vinculo.c.activo == True
    ).first()

    # 3. Asignamos el curso al objeto alumno (FastAPI/Pydantic se encargan del resto)
    alumno.curso_actual = curso_actual
    
    return alumno

# =================================================================
# 3. MODIFICAR ALUMNO (PATCH)
# =================================================================
@router.patch("/{id_alumno}", response_model=schemas.actores.AlumnoOut)
def modificar_alumno(
    id_alumno: int,
    alumno_data: schemas.actores.AlumnoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    query = db.query(models.actores.Alumno).filter(models.actores.Alumno.id_alumno == id_alumno)
    alumno_db = query.first()

    if not alumno_db:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")

    # Extraer datos enviados (ignorando los no definidos)
    update_data = alumno_data.model_dump(exclude_unset=True)

    # Lógica para actualizar Tutores
    if "tutores" in update_data:
        nuevos_vinculos = update_data.pop("tutores")
        
        # 1. Borrar vínculos viejos
        db.query(models.actores.AlumnoTutor).filter(
            models.actores.AlumnoTutor.id_alumno == id_alumno
        ).delete()
        
        # 2. Insertar vínculos nuevos
        for vinculo in nuevos_vinculos:
            # Aquí v es un diccionario porque viene de model_dump()
            nuevo_v = models.actores.AlumnoTutor(
                id_alumno=id_alumno,
                id_tutor=vinculo["id_tutor"],
                parentesco=vinculo["parentesco"],
                es_principal=vinculo["es_principal"]
            )
            db.add(nuevo_v)

    # Actualizar campos directos del Alumno (nombre, fecha_nac, etc.)
    if update_data:
        query.update(update_data)

    try:
        db.commit()
        db.refresh(alumno_db)
        return alumno_db
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")