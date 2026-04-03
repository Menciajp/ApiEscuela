from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/infraestructura",
    tags=["Infraestructura (Direcciones y Asistencias)"]
)

# --- ENDPOINTS PARA DIRECCIONES ---

@router.post("/direcciones", response_model=schemas.infraestructura.DireccionOut, status_code=status.HTTP_201_CREATED)
def crear_direccion(
    direccion: schemas.infraestructura.DireccionCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Registra una nueva dirección en el sistema.
    """
    nueva_direccion = models.infraestructura.Direccion(**direccion.model_dump())
    
    try:
        db.add(nueva_direccion)
        db.commit()
        db.refresh(nueva_direccion)
        return nueva_direccion
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al registrar la dirección: {str(e)}"
        )

@router.get("/direcciones/buscar", response_model=List[schemas.infraestructura.DireccionOut])
def buscar_direcciones(
    calle: Optional[str] = None,
    numero: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(auth.RoleChecker(["SUDO", "ADMIN"]))
):
    """
    Busca direcciones específicas usando parámetros de consulta.
    Ejemplo: /infraestructura/direcciones/buscar?calle=Marconi&numero=3328
    """
    query = db.query(models.infraestructura.Direccion)

    if calle:
        # ilike permite buscar sin importar mayúsculas/minúsculas
        query = query.filter(models.infraestructura.Direccion.calle.ilike(f"%{calle}%"))
    
    if numero:
        query = query.filter(models.infraestructura.Direccion.numero == numero)

    resultados = query.all()
    
    if not resultados:
        raise HTTPException(
            status_code=404, 
            detail="No se encontraron direcciones con los criterios proporcionados."
        )
        
    return resultados

@router.get("/direcciones/{id_direccion}", response_model=schemas.infraestructura.DireccionOut)
def obtener_direccion(
    id_direccion: int, 
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user_data) # Cualquier usuario logueado puede consultar
):
    direccion = db.query(models.infraestructura.Direccion).filter(
        models.infraestructura.Direccion.id_direccion == id_direccion
    ).first()
    
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    
    return direccion
