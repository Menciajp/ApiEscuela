from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func,extract
from datetime import date
from typing import List, Optional
from datetime import timedelta

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/asistencias",
    tags=["Gestión de Asistencias"]
)

# =================================================================
# 1. TOMA DE ASISTENCIA (CARGA MASIVA)
# =================================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
def tomar_asistencia_en_lote(
    asistencias: List[schemas.infraestructura.AsistenciaCreate],
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["PRECEPTOR", "ADMIN", "SUDO"]))
):
    if not asistencias:
        raise HTTPException(status_code=400, detail="No se enviaron datos.")

    # --- 1. VALIDACIÓN ÚNICA DE FECHA ---
    fecha_comun = asistencias[0].fecha
    # A. Validar Fin de Semana 
    if fecha_comun.weekday() >= 5:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede tomar asistencia: {fecha_comun} es fin de semana."
        )
    # B. Validar Feriado 
    feriado = db.query(models.academia.Feriado).filter(
        models.academia.Feriado.fecha == fecha_comun
    ).first()
    if feriado:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede tomar asistencia: {fecha_comun} es feriado ({feriado.descripcion})."
        )   
    # --- 2. PROCESAMIENTO EN LOTE ---
    procesados = 0
    for data in asistencias:
        # Lógica de Asistencia Implícita:
        if data.tipo_asistencia.upper() == "PRESENTE":
            pass
        else:
            nuevo = models.infraestructura.Asistencia(**data.model_dump())
            db.add(nuevo)    
        procesados += 1

    try:
        db.commit()
        return {"message": f"Planilla del {fecha_comun} procesada. Novedades: {procesados}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al guardar la asistencia.")

# =================================================================
# 2. CONSULTAS DE ASISTENCIA
# =================================================================

@router.get("/curso/{id_curso}/planilla", response_model=List[schemas.infraestructura.PlanillaAsistenciaOut])
def obtener_planilla_diaria(
    id_curso: int,
    fecha: date = date.today(), # FastAPI toma el parámetro ?fecha=YYYY-MM-DD o usa HOY por defecto
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_data)
):
    """
    Retorna la planilla del día. 
    Lanza error si es fin de semana o feriado.
    """
    # --- 1. VALIDACIÓN DE DÍA NO LECTIVO ---
    if fecha.weekday() >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fecha solicitada ({fecha}) corresponde a un fin de semana."
        )
    feriado = db.query(models.academia.Feriado).filter(
        models.academia.Feriado.fecha == fecha
    ).first()
    
    if feriado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fecha {fecha} es feriado: {feriado.descripcion}."
        )

    # --- 2. RECUPERAR ALUMNOS Y NOVEDADES ---

    tabla_vinculo = models.academia.alumno_integra_curso
    alumnos = db.query(models.actores.Alumno).join(
        tabla_vinculo, models.actores.Alumno.id_alumno == tabla_vinculo.c.id_alumno
    ).filter(
        tabla_vinculo.c.id_curso == id_curso,
        tabla_vinculo.c.activo == True
    ).order_by(models.actores.Alumno.apellido).all()

    if not alumnos:
        return []

    # Traer inasistencias/novedades grabadas (AUSENTE, TARDANZA, etc.)
    asistencias_reales = db.query(models.infraestructura.Asistencia).filter(
        models.infraestructura.Asistencia.id_curso == id_curso,
        models.infraestructura.Asistencia.fecha == fecha
    ).all()

    # Mapeo rápido para el cruce: {id_alumno: tipo_asistencia}
    mapa_novedades = {a.id_alumno: a.tipo_asistencia for a in asistencias_reales}

    # --- 3. CONSTRUCCIÓN DE LA RESPUESTA ---
    resultado = []
    for alu in alumnos:
        # Si no hay registro en la tabla de asistencia, por defecto es PRESENTE
        estado_final = mapa_novedades.get(alu.id_alumno, "PRESENTE")
        
        resultado.append({
            "id_alumno": alu.id_alumno,
            "nombre": alu.nombre,
            "apellido": alu.apellido,
            "estado": estado_final
        })

    return resultado

@router.get(
    "/alumno/{id_alumno}/historial", 
    response_model=schemas.infraestructura.HistorialAlumnoOut # <--- Esto activa la magia en Swagger
)
def consultar_historial_alumno(
    id_alumno: int,
    fecha_inicio: date,
    fecha_fin: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_data)
):
    """
    Consulta dinámica:
    1. Extrae el año de la fecha_inicio proporcionada.
    2. Devuelve el detalle día por día del rango (sin feriados/findes).
    3. Devuelve todas las inasistencias grabadas en la DB de ese mismo año.
    """
    # 1. Validar Alumno
    alumno = db.query(models.actores.Alumno).get(id_alumno)
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    # 2. DETERMINAR EL AÑO DINÁMICAMENTE
    anio_consulta = fecha_inicio.year

    # 3. Buscar el Ciclo Lectivo de ese año para conocer los límites y feriados
    ciclo = db.query(models.academia.CicloLectivo).filter(
        extract('year', models.academia.CicloLectivo.fecha_inicio) == anio_consulta
    ).first()

    if not ciclo:
        raise HTTPException(
            status_code=404, 
            detail=f"No existe un Ciclo Lectivo registrado para el año {anio_consulta}"
        )

    # Obtener feriados de ese ciclo
    feriados = db.query(models.academia.Feriado).filter(
        models.academia.Feriado.id_ciclo == ciclo.id_ciclo
    ).all()
    set_feriados = {f.fecha for f in feriados}

    # 4. Obtener TODAS las novedades (Ausentes/Tardanzas) del año completo
    # Filtramos por las fechas del ciclo lectivo encontrado
    novedades_anio = db.query(models.infraestructura.Asistencia).filter(
        models.infraestructura.Asistencia.id_alumno == id_alumno,
        models.infraestructura.Asistencia.fecha >= ciclo.fecha_inicio,
        models.infraestructura.Asistencia.fecha <= ciclo.fecha_fin
    ).order_by(models.infraestructura.Asistencia.fecha.asc()).all()

    # Mapeo para el cruce del rango: {fecha: tipo_asistencia}
    mapa_novedades = {n.fecha: n.tipo_asistencia for n in novedades_anio}

    # 5. Generar el detalle del rango (Solo días lectivos)
    detalle_rango = []
    fecha_aux = fecha_inicio
    
    while fecha_aux <= fecha_fin:
        # Reglas: No Sábados(5), No Domingos(6), No Feriados
        if fecha_aux.weekday() < 5 and fecha_aux not in set_feriados:
            # Si no hay registro en la DB, es PRESENTE
            estado = mapa_novedades.get(fecha_aux, "PRESENTE")
            detalle_rango.append({
                "fecha": fecha_aux,
                "estado": estado
            })
        fecha_aux += timedelta(days=1)

    return {
            "alumno": f"{alumno.apellido}, {alumno.nombre}",
            "anio_escolar": anio_consulta,
            "rango": {
                "desde": fecha_inicio,
                "hasta": fecha_fin,
                "detalle_diario": detalle_rango
            },
            "historial_novedades_anual": novedades_anio 
    }

@router.patch("/modificar", status_code=status.HTTP_200_OK)
def modificar_asistencia_alumno(
    asistencia_data: schemas.infraestructura.AsistenciaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["PRECEPTOR", "ADMIN", "SUDO"]))
):
    """
    Sincroniza el estado de asistencia de un alumno para una fecha específica:
    - PRESENTE: Borra el registro (asistencia implícita).
    - OTRO: Crea o actualiza el registro existente.
    """
    # Buscamos si ya existe una novedad (Ausente/Tardanza) para ese alumno y fecha
    registro_existente = db.query(models.infraestructura.Asistencia).filter(
        models.infraestructura.Asistencia.id_alumno == asistencia_data.id_alumno,
        models.infraestructura.Asistencia.fecha == asistencia_data.fecha
    ).first()

    tipo_nuevo = asistencia_data.tipo_asistencia.upper()

    # --- CASO 1: Volver a 'PRESENTE' ---
    if tipo_nuevo == "PRESENTE":
        if registro_existente:
            db.delete(registro_existente)
            db.commit()
            return {"message": "Registro eliminado. El alumno ahora figura como Presente."}
        return {"message": "El alumno ya figuraba como Presente."}

    # --- CASO 2: Cargar o Modificar Falta/Tardanza ---
    if registro_existente:
        # Actualizamos los valores (ej: cambiar Ausente por Tardanza o cambiar justificación)
        registro_existente.tipo_asistencia = tipo_nuevo
        registro_existente.justificacion = asistencia_data.justificacion
        # Aseguramos que el curso sea el correcto por si hubo un error previo
        registro_existente.id_curso = asistencia_data.id_curso 
    else:
        # No existía registro (era un Presente implícito), creamos la novedad
        nuevo_registro = models.infraestructura.Asistencia(**asistencia_data.model_dump())
        db.add(nuevo_registro)

    try:
        db.commit()
        return {"message": f"Estado actualizado a {tipo_nuevo}."}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar la asistencia.")