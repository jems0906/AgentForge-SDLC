from typing import Annotated

from app.database import get_db
from app.models import Property, Tenant
from app.schemas import TenantInput, TenantRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantRead])
def list_tenants(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(Tenant).order_by(Tenant.id)).all()


@router.post("", response_model=TenantRead, status_code=201)
def create_tenant(payload: TenantInput, db: Annotated[Session, Depends(get_db)]):
    if db.get(Property, payload.property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant
