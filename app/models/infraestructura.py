from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from datetime import date
from typing import List, Optional  
from .actores import Alumno, Tutor

class Direccion(Base):
    __tablename__ = "direccion"
    id_direccion: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    calle: Mapped[str] = mapped_column(String(100))
    numero: Mapped[Optional[str]] = mapped_column(String(10))
    dpto: Mapped[Optional[str]] = mapped_column(String(10))

    # Relaciones inversas
    alumnos: Mapped[List["Alumno"]] = relationship(back_populates="direccion")
    tutores: Mapped[List["Tutor"]] = relationship(back_populates="direccion")

class Asistencia(Base):
    __tablename__ = "asistencia"
    
    id_asistencia: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo_asistencia: Mapped[str] = mapped_column(String(50)) # Presente, Ausente, etc.
    justificacion: Mapped[bool] = mapped_column(default=False)
    fecha: Mapped[date] = mapped_column(Date)
    
    # Claves Foráneas
    id_alumno: Mapped[int] = mapped_column(ForeignKey("alumno.id_alumno", ondelete="CASCADE"))
    id_curso: Mapped[int] = mapped_column(ForeignKey("curso.id_curso", ondelete="CASCADE")) # <--- NUEVO

    # Relaciones
    alumno: Mapped["Alumno"] = relationship(back_populates="asistencias")
    curso: Mapped["Curso"] = relationship() 