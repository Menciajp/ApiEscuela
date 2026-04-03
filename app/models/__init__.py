from ..database import Base
from .infraestructura import Direccion, Asistencia
from .actores import Alumno, Tutor, Empleado, AlumnoTutor  # AlumnoTutor es una Clase
from .academia import CicloLectivo, Curso, Feriado, alumno_integra_curso # es un objeto Table

# Exportamos todo
__all__ = [
    "Base", 
    "Direccion", 
    "Asistencia", 
    "Alumno", 
    "Tutor", 
    "Empleado", 
    "AlumnoTutor",         # Importante para gestionar parentescos
    "CicloLectivo",
    "Curso",
    "Feriado",
    "alumno_integra_curso" # Opcional, pero bueno tenerlo registrado
]