from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.leases import LEASES
from app.services.payment_validation import validate_rent_payment


router = APIRouter(prefix="/payments", tags=["payments"])
PAYMENTS = []


class PaymentInput(BaseModel):
    lease_id: int = Field(ge=1)
    amount: int = Field(gt=0)


@router.get("")
def list_payments():
    return PAYMENTS


@router.post("", status_code=201)
def validate_payment(payload: PaymentInput):
    lease = next((item for item in LEASES if item["id"] == payload.lease_id), None)
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease not found")
    if not validate_rent_payment(payload.amount, lease["monthly_rent"]):
        raise HTTPException(status_code=422, detail="Payment exceeds validation limits")
    payment = {"id": max((item["id"] for item in PAYMENTS), default=0) + 1, **payload.model_dump(), "status": "validated"}
    PAYMENTS.append(payment)
    return payment
