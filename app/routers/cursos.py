from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from typing import List, Optional

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/cursos",
    tags=["Gestión de Cursos"]
)

# --- LISTAR CURSOS (Con lógica de Rol y Año Actual) ---
@router.get("/", response_model=List[schemas.academia.CursoOut])
def listar_cursos(
    id_ciclo: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_data)
):
    username = current_user.get("username")
    rol_usuario = current_user.get("rol").upper()

    # 1. Determinar el Ciclo (Por ID o Año Actual)
    target_ciclo_id = id_ciclo
    if not target_ciclo_id:
        anio_actual = date.today().year
        ciclo_actual = db.query(models.academia.CicloLectivo).filter(
            extract('year', models.academia.CicloLectivo.fecha_inicio) == anio_actual
        ).first()
        if not ciclo_actual: return []
        target_ciclo_id = ciclo_actual.id_ciclo

    # 2. Query Base
    query = db.query(models.academia.Curso).filter(models.academia.Curso.id_ciclo == target_ciclo_id)

    # 3. Filtros por Rol
    if rol_usuario in ["SUDO", "ADMIN"]:
        pass
    elif rol_usuario == "PRECEPTOR":
        empleado = db.query(models.actores.Empleado).filter(models.actores.Empleado.nombre_usr == username).first()
        if not empleado: raise HTTPException(status_code=404, detail="Empleado no encontrado.")
        query = query.filter(models.academia.Curso.id_empleado == empleado.id_empleado)
    else:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver cursos.")

    return query.all()

# --- CREAR CURSO ---
@router.post("/", response_model=schemas.academia.CursoOut, status_code=status.HTTP_201_CREATED)
def crear_curso(
    curso: schemas.academia.CursoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    ciclo = db.query(models.academia.CicloLectivo).get(curso.id_ciclo)
    if not ciclo: raise HTTPException(status_code=404, detail="Ciclo Lectivo no encontrado.")

    # Validar duplicado en el mismo ciclo
    existe = db.query(models.academia.Curso).filter(
        models.academia.Curso.nombre == curso.nombre,
        models.academia.Curso.division == curso.division,
        models.academia.Curso.id_ciclo == curso.id_ciclo
    ).first()
    if existe: raise HTTPException(status_code=400, detail="El curso y división ya existen en este ciclo.")

    nuevo_curso = models.academia.Curso(**curso.model_dump())
    db.add(nuevo_curso)
    db.commit()
    db.refresh(nuevo_curso)
    return nuevo_curso

# --- MODIFICAR CURSO (Asignar Preceptor, etc.) ---
@router.patch("/{id_curso}", response_model=schemas.academia.CursoOut)
def modificar_curso(
    id_curso: int,
    curso_data: schemas.academia.CursoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    query = db.query(models.academia.Curso).filter(models.academia.Curso.id_curso == id_curso)
    curso_db = query.first()
    if not curso_db: raise HTTPException(status_code=404, detail="Curso no encontrado.")

    update_dict = curso_data.model_dump(exclude_unset=True)

    if "id_empleado" in update_dict and update_dict["id_empleado"] is not None:
        empleado = db.query(models.actores.Empleado).get(update_dict["id_empleado"])
        if not empleado: raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    query.update(update_dict)
    db.commit()
    db.refresh(curso_db)
    return curso_db

# --- MATRICULAR ALUMNO ---
@router.post("/matricular", status_code=status.HTTP_201_CREATED)
def matricular_alumno(
    inscripcion: schemas.academia.InscripcionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    alumno = db.query(models.actores.Alumno).get(inscripcion.id_alumno)
    curso = db.query(models.academia.Curso).get(inscripcion.id_curso)
    if not alumno or not curso: raise HTTPException(status_code=404, detail="Alumno o Curso no encontrado.")

    # Desactivar inscripciones previas
    tabla_vinculo = models.academia.alumno_integra_curso
    db.execute(
        tabla_vinculo.update().where(tabla_vinculo.c.id_alumno == inscripcion.id_alumno).values(activo=False)
    )

    # Insertar nueva matrícula
    try:
        db.execute(tabla_vinculo.insert().values(id_alumno=inscripcion.id_alumno, id_curso=inscripcion.id_curso, activo=True))
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error en la matriculación. Verifique si ya existe el registro.")

    return {"message": f"Alumno {alumno.nombre} matriculado con éxito en {curso.nombre} {curso.division}"}

# --- CONSULTAR ALUMNOS POR CURSO---
@router.get("/{id_curso}/alumnos", response_model=List[schemas.actores.AlumnoOut])
def listar_alumnos_del_curso(
    id_curso: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["SUDO", "ADMIN", "PRECEPTOR"]))
) :
    """
    Obtiene la lista de alumnos ACTIVOS en un curso determinado.
    """
    curso_existe = db.query(models.academia.Curso).filter(
        models.academia.Curso.id_curso == id_curso
    ).first()
    
    if not curso_existe:
        raise HTTPException(status_code=404, detail="El curso solicitado no existe.")

    # Consulta a la tabla Alumno cruzando con la tabla intermedia
    tabla_vinculo = models.academia.alumno_integra_curso
    
    alumnos = db.query(models.actores.Alumno).join(
        tabla_vinculo, 
        models.actores.Alumno.id_alumno == tabla_vinculo.c.id_alumno
    ).filter(
        tabla_vinculo.c.id_curso == id_curso,
        tabla_vinculo.c.activo == True
    ).order_by(
        models.actores.Alumno.apellido, 
        models.actores.Alumno.nombre
    ).all()

    return alumnos    