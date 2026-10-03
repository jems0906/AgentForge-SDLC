from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.properties import PROPERTIES
from app.services.maintenance import normalize_priority


router = APIRouter(prefix="/maintenance", tags=["maintenance"])
TICKETS = []


class TicketInput(BaseModel):
    property_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=180)
    priority: str = "normal"


@router.get("")
def list_tickets():
    return TICKETS


@router.post("", status_code=201)
def create_ticket(payload: TicketInput):
    if not any(item["id"] == payload.property_id for item in PROPERTIES):
        raise HTTPException(status_code=404, detail="Property not found")
    try:
        priority = normalize_priority(payload.priority)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    ticket = {"id": max((item["id"] for item in TICKETS), default=0) + 1, "status": "open", **payload.model_dump(exclude={"priority"}), "priority": priority}
    TICKETS.append(ticket)
    return ticket
