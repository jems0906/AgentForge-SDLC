from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.tenants import TENANTS
from app.services.notification_service import lease_renewal_due


router = APIRouter(prefix="/leases", tags=["leases"])
LEASES = []


class LeaseInput(BaseModel):
    tenant_id: int = Field(ge=1)
    starts_on: date
    ends_on: date
    monthly_rent: int = Field(gt=0)


@router.get("")
def list_leases():
    return LEASES


@router.post("", status_code=201)
def create_lease(payload: LeaseInput):
    if not any(item["id"] == payload.tenant_id for item in TENANTS):
        raise HTTPException(status_code=404, detail="Tenant not found")
    if payload.ends_on <= payload.starts_on:
        raise HTTPException(status_code=422, detail="Lease end date must follow its start date")
    lease = {"id": max((item["id"] for item in LEASES), default=0) + 1, **payload.model_dump(mode="json")}
    LEASES.append(lease)
    return lease


@router.get("/{lease_id}/renewal-due")
def renewal_due(lease_id: int, today: date | None = None):
    lease = next((item for item in LEASES if item["id"] == lease_id), None)
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease not found")
    return {"lease_id": lease_id, "due": lease_renewal_due(date.fromisoformat(lease["ends_on"]), today)}
