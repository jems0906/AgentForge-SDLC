from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.properties import PROPERTIES


router = APIRouter(prefix="/tenants", tags=["tenants"])
TENANTS = []


class TenantInput(BaseModel):
    property_id: int = Field(ge=1)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=240)


@router.get("")
def list_tenants():
    return TENANTS


@router.post("", status_code=201)
def create_tenant(payload: TenantInput):
    if not any(item["id"] == payload.property_id for item in PROPERTIES):
        raise HTTPException(status_code=404, detail="Property not found")
    tenant = {"id": max((item["id"] for item in TENANTS), default=0) + 1, **payload.model_dump()}
    TENANTS.append(tenant)
    return tenant
