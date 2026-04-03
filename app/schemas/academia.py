from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

# --- SCHEMAS PARA CICLO LECTIVO ---
class CicloLectivoBase(BaseModel):
    fecha_inicio: date
    fecha_fin: date

class CicloLectivoCreate(CicloLectivoBase):
    """Esquema para crear un año escolar"""
    pass

class CicloLectivoOut(CicloLectivoBase):
    id_ciclo: int
    
    class Config:
        from_attributes = True

# --- SCHEMAS PARA FERIADO ---
class FeriadoBase(BaseModel):
    fecha: date
    descripcion: str = Field(..., max_length=255)
    id_ciclo: int

class FeriadoCreate(FeriadoBase):
    """Esquema para registrar un día feriado"""
    pass

class FeriadoUpdate(BaseModel):
    fecha: Optional[date] = None
    descripcion: Optional[str] = None
    id_ciclo: Optional[int] = None

class FeriadoOut(FeriadoBase):
    id_feriado: int

    class Config:
        from_attributes = True

# --- SCHEMAS PARA CURSO ---
class CursoBase(BaseModel):
    nombre: str = Field(..., max_length=50, description="Nombre de la materia o grado")
    division: str = Field(..., max_length=50, description="Ej: 'A', 'Turno Mañana', etc.")
    id_empleado: Optional[int] = Field(None, description="ID del docente a cargo")
    id_ciclo: int

class CursoCreate(CursoBase):
    """Esquema para registrar un nuevo curso"""
    pass

class CursoUpdate(BaseModel):
    """Esquema para actualizaciones parciales de un curso"""
    nombre: Optional[str] = Field(None, max_length=50)
    division: Optional[str] = Field(None, max_length=50)
    id_empleado: Optional[int] = Field(None, description="ID del nuevo preceptor/docente")
    id_ciclo: Optional[int] = Field(None, description="Cambiar el curso de ciclo lectivo")

    class Config:
        from_attributes = True

class CursoOut(CursoBase):
    id_curso: int

    class Config:
        from_attributes = True
        
# --- SCHEMAS PARA inscripcion de alumno ---
class InscripcionCreate(BaseModel):
    """Esquema para matricular un alumno en un curso"""
    id_alumno: int
    id_curso: int

class InscripcionOut(InscripcionCreate):
    activo: bool

    class Config:
        from_attributes = True


