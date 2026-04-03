from sqlalchemy import String, ForeignKey, Date, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from datetime import date
from typing import List, Optional

# --- 9. Tabla Intermedia: Alumno_Integra_Curso (Muchos a Muchos) ---
# La definimos como Table porque no necesitamos atributos extra en la relación
alumno_integra_curso = Table(
    "alumno_integra_curso",
    Base.metadata,
    Column("id_alumno", ForeignKey("alumno.id_alumno", ondelete="CASCADE"), primary_key=True),
    Column("id_curso", ForeignKey("curso.id_curso", ondelete="CASCADE"), primary_key=True),
    Column("activo", Boolean, default=True)
)

class CicloLectivo(Base):
    __tablename__ = "ciclo_lectivo"

    id_ciclo: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)

    # Relaciones
    cursos: Mapped[List["Curso"]] = relationship(back_populates="ciclo")
    feriados: Mapped[List["Feriado"]] = relationship(back_populates="ciclo")

class Curso(Base):
    __tablename__ = "curso"

    id_curso: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    division: Mapped[str] = mapped_column(String(50), nullable=False)
    id_empleado: Mapped[Optional[int]] = mapped_column(ForeignKey("empleado.id_empleado"))
    id_ciclo: Mapped[int] = mapped_column(ForeignKey("ciclo_lectivo.id_ciclo"))

    # Relaciones
    empleado: Mapped[Optional["Empleado"]] = relationship(back_populates="cursos")
    ciclo: Mapped["CicloLectivo"] = relationship(back_populates="cursos")
    alumnos: Mapped[List["Alumno"]] = relationship(
        secondary=alumno_integra_curso, 
        back_populates="cursos"
    )

class Feriado(Base):
    __tablename__ = "feriados"

    id_feriado: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    id_ciclo: Mapped[int] = mapped_column(ForeignKey("ciclo_lectivo.id_ciclo", ondelete="CASCADE"))

    ciclo: Mapped["CicloLectivo"] = relationship(back_populates="feriados")