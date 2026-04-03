from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from . import academia
from .infraestructura import AsistenciaOut


# =================================================================
# 1. SCHEMAS DE APOYO (Para relaciones con datos extra)
# =================================================================

class TutorVinculo(BaseModel):
    """Representa la unión entre Alumno y Tutor con sus campos extra"""
    id_tutor: int
    parentesco: str
    es_principal: bool = False

    class Config:
        from_attributes = True

# =================================================================
# 2. SCHEMA BASE DE PERSONA
# =================================================================

class PersonaBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    

# =================================================================
# 3. TUTOR
# =================================================================

class TutorBase(PersonaBase):
    telefono: Optional[str] = None
    nombre_usr: str
    id_direccion: int

class TutorCreate(TutorBase):
    contrasenia: str = Field(..., min_length=8, description="La clave debe tener al menos 8 caracteres")

class TutorOut(TutorBase):
    id_tutor: int
    class Config:
        from_attributes = True

class TutorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    nombre_usr: Optional[str] = None
    contrasenia: Optional[str] = None
    id_direccion: Optional[int] = None

# =================================================================
# 4. EMPLEADO
# =================================================================

class EmpleadoBase(PersonaBase):
    telefono: Optional[str] = None
    nombre_usr: str
    rol: str

class EmpleadoCreate(EmpleadoBase):
    contrasenia: str = Field(..., min_length=8)

class EmpleadoOut(EmpleadoBase):
    id_empleado: int
    class Config:
        from_attributes = True

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    nombre_usr: Optional[str] = None
    rol: Optional[str] = None
    contrasenia: Optional[str] = None

# =================================================================
# 5. ALUMNO
# =================================================================

class AlumnoBase(PersonaBase):
    sexo: Optional[str] = None
    fech_nac: date
    nacionalidad: Optional[str] = None
    id_direccion: int

class AlumnoCreate(AlumnoBase):
    # En lugar de List[int], enviamos la lista de vínculos con parentesco
    tutores: List[TutorVinculo]

class AlumnoOut(AlumnoBase):
    id_alumno: int
    # Para mostrar los tutores con su parentesco al consultar
    curso_actual: Optional[academia.CursoOut] = None
    tutores_detalles: List[TutorVinculo] = Field(..., alias="tutores_detalles")

    class Config:
        from_attributes = True
        populate_by_name = True # Permite usar el alias 'tutores_detalles'

class AlumnoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    sexo: Optional[str] = None
    dni: Optional[str] = None
    fech_nac: Optional[date] = None
    nacionalidad: Optional[str] = None
    id_direccion: Optional[int] = None
    # Permite actualizar la lista de tutores y sus parentescos
    tutores: Optional[List[TutorVinculo]] = None

    class Config:
        from_attributes = True

class TuteladoAsistenciaOut(BaseModel):
    id_alumno: int
    nombre: str
    apellido: str
    dni: str
    inasistencias: List[AsistenciaOut]