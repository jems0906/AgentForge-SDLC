from datetime import date
from typing import Annotated

from app.database import get_db
from app.models import Lease, Tenant
from app.schemas import LeaseInput, LeaseRead
from app.services.notification_service import lease_renewal_due
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/leases", tags=["leases"])


@router.get("", response_model=list[LeaseRead])
def list_leases(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(Lease).order_by(Lease.id)).all()


@router.post("", response_model=LeaseRead, status_code=201)
def create_lease(payload: LeaseInput, db: Annotated[Session, Depends(get_db)]):
    if db.get(Tenant, payload.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if payload.ends_on <= payload.starts_on:
        raise HTTPException(status_code=422, detail="Lease end date must follow its start date")
    lease = Lease(**payload.model_dump())
    db.add(lease)
    db.commit()
    db.refresh(lease)
    return lease


@router.get("/{lease_id}/renewal-due")
def renewal_due(lease_id: int, db: Annotated[Session, Depends(get_db)], today: date | None = None):
    lease = db.get(Lease, lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease not found")
    return {"lease_id": lease_id, "due": lease_renewal_due(lease.ends_on, today)}
