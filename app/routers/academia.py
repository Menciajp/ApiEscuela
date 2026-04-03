import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import Extract
from datetime import date
from typing import List, Optional
from datetime import date
from .. import models, schemas, auth
from ..database import get_db, SessionLocal 

router = APIRouter(
    prefix="/academia",
    tags=["Academia: Ciclo Lectivo y Feriados"]
)

# =================================================================
# 1. TAREA DE FONDO (Background Task)
# =================================================================

def tarea_importar_feriados(f_inicio: date, f_fin: date, id_ciclo: int, db_factory):
    print(f"\n[TASK] === INICIO FILTRADO: {f_inicio} al {f_fin} ===")
    db = db_factory()
    anio = f_inicio.year
    
    try:
        url = f"https://api.argentinadatos.com/v1/feriados/{anio}"
        # follow_redirects=True para evitar el 301
        response = httpx.get(url, timeout=15.0, follow_redirects=True)
        
        if response.status_code == 200:
            datos = response.json()
            contador = 0
            
            for f in datos:
                fecha_f = date.fromisoformat(f['fecha'])
                
                # --- EL FILTRO CLAVE ---
                # Solo procesamos si el feriado cae DENTRO del ciclo lectivo
                if f_inicio <= fecha_f <= f_fin:
                    
                    # Evitar duplicados
                    existe = db.query(models.academia.Feriado).filter(
                        models.academia.Feriado.fecha == fecha_f,
                        models.academia.Feriado.id_ciclo == id_ciclo
                    ).first()
                    
                    if not existe:
                        nuevo_f = models.academia.Feriado(
                            fecha=fecha_f,
                            descripcion=f['nombre'],
                            id_ciclo=id_ciclo
                        )
                        db.add(nuevo_f)
                        contador += 1
            
            db.commit()
            print(f"[TASK] ÉXITO: Se guardaron {contador} feriados dentro del rango escolar.")
        else:
            print(f"[TASK] ERROR API: {response.status_code}")

    except Exception as e:
        print(f"[TASK] ERROR CRÍTICO: {e}")
    finally:
        db.close()
        print("[TASK] === FIN DE TAREA ===\n")
# =================================================================
# 2. ENDPOINTS: CICLO LECTIVO
# =================================================================

@router.post("/ciclos", response_model=schemas.academia.CicloLectivoOut, status_code=status.HTTP_201_CREATED)
def crear_ciclo_lectivo(
    ciclo: schemas.academia.CicloLectivoCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    # A. Validaciones de fechas
    if ciclo.fecha_fin <= ciclo.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior.")

    superposicion = db.query(models.academia.CicloLectivo).filter(
        models.academia.CicloLectivo.fecha_inicio <= ciclo.fecha_fin,
        models.academia.CicloLectivo.fecha_fin >= ciclo.fecha_inicio
    ).first()

    if superposicion:
        raise HTTPException(status_code=400, detail="Las fechas se superponen con otro ciclo.")

    # B. Guardar en BD
    nuevo_ciclo = models.academia.CicloLectivo(**ciclo.model_dump())
    
    try:
        db.add(nuevo_ciclo)
        db.commit()
        db.refresh(nuevo_ciclo)

        # C. DISPARAR TAREA PASANDO EL AÑO DIRECTAMENTE
        # Extraemos el año de la fecha_inicio que ya tenemos en 'ciclo'
        anio_lectivo = ciclo.fecha_inicio.year
        background_tasks.add_task(
            tarea_importar_feriados, 
            ciclo.fecha_inicio, 
            ciclo.fecha_fin,    
            nuevo_ciclo.id_ciclo, 
            SessionLocal
        )

        return nuevo_ciclo
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ciclos", response_model=List[schemas.academia.CicloLectivoOut])
def listar_ciclos(db: Session = Depends(get_db)):
    return db.query(models.academia.CicloLectivo).order_by(models.academia.CicloLectivo.fecha_inicio.desc()).all()

# =================================================================
# 3. GESTIÓN MANUAL DE FERIADOS
# =================================================================
@router.post("/feriados", response_model=schemas.academia.FeriadoOut, status_code=status.HTTP_201_CREATED)
def crear_feriado_manual(
    feriado: schemas.academia.FeriadoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    # 1. Verificar que el ciclo exista
    ciclo = db.query(models.academia.CicloLectivo).get(feriado.id_ciclo)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo lectivo no encontrado")

    # 2. Validar que la fecha esté dentro del ciclo
    if not (ciclo.fecha_inicio <= feriado.fecha <= ciclo.fecha_fin):
        raise HTTPException(
            status_code=400, 
            detail=f"La fecha {feriado.fecha} está fuera del rango del ciclo ({ciclo.fecha_inicio} a {ciclo.fecha_fin})"
        )

    # 3. Verificar duplicados
    existe = db.query(models.academia.Feriado).filter(
        models.academia.Feriado.fecha == feriado.fecha,
        models.academia.Feriado.id_ciclo == feriado.id_ciclo
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un feriado registrado en esa fecha para este ciclo")

    nuevo_feriado = models.academia.Feriado(**feriado.model_dump())
    db.add(nuevo_feriado)
    db.commit()
    db.refresh(nuevo_feriado)
    return nuevo_feriado

@router.patch("/feriados/{id_feriado}", response_model=schemas.academia.FeriadoOut)
def modificar_feriado(
    id_feriado: int,
    feriado_data: schemas.academia.FeriadoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    query = db.query(models.academia.Feriado).filter(models.academia.Feriado.id_feriado == id_feriado)
    feriado_db = query.first()
    
    if not feriado_db:
        raise HTTPException(status_code=404, detail="Feriado no encontrado")

    update_dict = feriado_data.model_dump(exclude_unset=True)

    # 1. Si se intenta cambiar la fecha o el ciclo, validamos TODO
    if "fecha" in update_dict or "id_ciclo" in update_dict:
        nueva_fecha = update_dict.get("fecha", feriado_db.fecha)
        nuevo_ciclo_id = update_dict.get("id_ciclo", feriado_db.id_ciclo)

        ciclo = db.query(models.academia.CicloLectivo).get(nuevo_ciclo_id)
    
        # VALIDACIÓN CRÍTICA: ¿Existe el ciclo?
        if not ciclo:
            raise HTTPException(
                status_code=404, 
                detail=f"El Ciclo Lectivo con ID {nuevo_ciclo_id} no existe."
            )
        
        # A. Validar que la fecha caiga dentro del Ciclo Lectivo
        ciclo = db.query(models.academia.CicloLectivo).get(nuevo_ciclo_id)
        if not (ciclo.fecha_inicio <= nueva_fecha <= ciclo.fecha_fin):
            raise HTTPException(
                status_code=400, 
                detail=f"La fecha {nueva_fecha} queda fuera del rango del ciclo ({ciclo.fecha_inicio} a {ciclo.fecha_fin})"
            )

        # B. Validar que NO exista otro feriado en esa misma fecha/ciclo
        # IMPORTANTE: .filter(models.academia.Feriado.id_feriado != id_feriado)
        duplicado = db.query(models.academia.Feriado).filter(
            models.academia.Feriado.fecha == nueva_fecha,
            models.academia.Feriado.id_ciclo == nuevo_ciclo_id,
            models.academia.Feriado.id_feriado != id_feriado  # <--- No compararse con uno mismo
        ).first()

        if duplicado:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe otro feriado ('{duplicado.descripcion}') registrado para esa fecha"
            )

    # 2. Si pasó todas las pruebas, actualizamos
    query.update(update_dict)
    db.commit()
    db.refresh(feriado_db)
    return feriado_db

@router.delete("/feriados/{id_feriado}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_feriado(
    id_feriado: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    feriado = db.query(models.academia.Feriado).filter(models.academia.Feriado.id_feriado == id_feriado).first()
    if not feriado:
        raise HTTPException(status_code=404, detail="Feriado no encontrado")
    
    db.delete(feriado)
    db.commit()
    return None

