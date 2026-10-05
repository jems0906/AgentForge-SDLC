from typing import Annotated

from app.database import get_db
from app.models import Lease, RentPayment
from app.schemas import PaymentInput, PaymentRead
from app.services.payment_validation import validate_rent_payment
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead])
def list_payments(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(RentPayment).order_by(RentPayment.id)).all()


@router.post("", response_model=PaymentRead, status_code=201)
def validate_payment(payload: PaymentInput, db: Annotated[Session, Depends(get_db)]):
    lease = db.get(Lease, payload.lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease not found")
    if not validate_rent_payment(payload.amount, lease.monthly_rent):
        raise HTTPException(status_code=422, detail="Payment exceeds validation limits")
    payment = RentPayment(**payload.model_dump(), status="validated")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
