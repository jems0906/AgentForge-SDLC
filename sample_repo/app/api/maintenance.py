from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MaintenanceTicket, Property
from app.schemas import TicketInput, TicketRead
from app.services.maintenance import normalize_priority

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("", response_model=list[TicketRead])
def list_tickets(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(MaintenanceTicket).order_by(MaintenanceTicket.id)).all()


@router.post("", response_model=TicketRead, status_code=201)
def create_ticket(payload: TicketInput, db: Annotated[Session, Depends(get_db)]):
    if db.get(Property, payload.property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    try:
        priority = normalize_priority(payload.priority)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    ticket = MaintenanceTicket(property_id=payload.property_id, title=payload.title, priority=priority)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
