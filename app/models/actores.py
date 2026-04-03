from sqlalchemy import String, ForeignKey, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from datetime import date
from typing import List, Optional

# =================================================================
# 1. TABLA INTERMEDIA (Association Object)
# =================================================================

class AlumnoTutor(Base):
    """
    Tabla de asociación con datos extra entre Alumno y Tutor.
    """
    __tablename__ = "alumno_tutor"
    
    id_alumno: Mapped[int] = mapped_column(
        ForeignKey("alumno.id_alumno", ondelete="CASCADE"), 
        primary_key=True
    )
    id_tutor: Mapped[int] = mapped_column(
        ForeignKey("tutor.id_tutor", ondelete="CASCADE"), 
        primary_key=True
    )
    parentesco: Mapped[Optional[str]] = mapped_column(String(50))
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relaciones hacia los "padres"
    alumno: Mapped["Alumno"] = relationship(back_populates="tutores_detalles")
    tutor: Mapped["Tutor"] = relationship(back_populates="alumnos_detalles")


# =================================================================
# 2. MODELOS PRINCIPALES
# =================================================================

class Empleado(Base):
    __tablename__ = "empleado"

    id_empleado: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_usr: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    contrasenia: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    rol: Mapped[str] = mapped_column(String(15), nullable=False)

    # Relación con Curso (se define en academia.py)
    cursos: Mapped[List["Curso"]] = relationship(back_populates="empleado")


class Tutor(Base):
    __tablename__ = "tutor"

    id_tutor: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_usr: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    contrasenia: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    id_direccion: Mapped[int] = mapped_column(ForeignKey("direccion.id_direccion"))

    # Relaciones
    direccion: Mapped["Direccion"] = relationship(back_populates="tutores")
    
    # Conexión a través de la tabla intermedia
    alumnos_detalles: Mapped[List["AlumnoTutor"]] = relationship(
        back_populates="tutor", 
        cascade="all, delete-orphan"
    )


class Alumno(Base):
    __tablename__ = "alumno"

    id_alumno: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    sexo: Mapped[Optional[str]] = mapped_column(String(20))
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    fech_nac: Mapped[date] = mapped_column(Date, nullable=False)
    nacionalidad: Mapped[Optional[str]] = mapped_column(String(50))
    id_direccion: Mapped[int] = mapped_column(ForeignKey("direccion.id_direccion"))

    # Relaciones básicas
    direccion: Mapped["Direccion"] = relationship(back_populates="alumnos")
    asistencias: Mapped[List["Asistencia"]] = relationship(back_populates="alumno")
    
    # Relación muchos a muchos con Tutores (con campos extra)
    tutores_detalles: Mapped[List["AlumnoTutor"]] = relationship(
        back_populates="alumno", 
        cascade="all, delete-orphan"
    )
    
    # Relación muchos a muchos con Cursos (Suponiendo tabla 'alumno_integra_curso' simple)
    cursos: Mapped[List["Curso"]] = relationship(
        secondary="alumno_integra_curso", 
        back_populates="alumnos"
    )