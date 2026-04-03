from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List


# --- SCHEMAS PARA DIRECCION ---
class DireccionBase(BaseModel):
    calle: str = Field(..., max_length=100, description="Nombre de la calle o avenida")
    numero: Optional[str] = Field(None, max_length=10, description="Altura o número de casa")
    dpto: Optional[str] = Field(None, max_length=10, description="Departamento, piso o torre")

class DireccionCreate(DireccionBase):
    """Esquema para crear una nueva dirección"""
    pass

class DireccionOut(DireccionBase):
    """Esquema para mostrar los datos de una dirección"""
    id_direccion: int

    class Config:
        from_attributes = True


# --- SCHEMAS PARA ASISTENCIA ---
class AsistenciaBase(BaseModel):
    tipo_asistencia: str = Field(..., description="Ej: Ausente, Tardanza")
    justificacion: bool = Field(default=False)
    fecha: date = Field(default_factory=date.today)
    id_alumno: int
    id_curso: int 

class AsistenciaCreate(AsistenciaBase):
    pass

class AsistenciaOut(AsistenciaBase):
    id_asistencia: int
    class Config:
        from_attributes = True

class PlanillaAsistenciaOut(BaseModel):
    id_alumno: int
    nombre: str
    apellido: str
    estado: str

# Esquema para cada día del rango consultado
class DetalleDiarioAsistencia(BaseModel):
    fecha: date
    estado: str

# Esquema para el objeto del rango
class RangoConsultaAsistencia(BaseModel):
    desde: date
    hasta: date
    detalle_diario: List[DetalleDiarioAsistencia]

# Esquema PRINCIPAL de respuesta para Swagger
class HistorialAlumnoOut(BaseModel):
    alumno: str
    anio_escolar: int
    rango: RangoConsultaAsistencia
    # Reutilizamos AsistenciaOut para los registros reales de la DB
    historial_novedades_anual: List[AsistenciaOut] 

    class Config:
        from_attributes = True