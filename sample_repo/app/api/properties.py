from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/properties", tags=["properties"])
PROPERTIES = [{"id": 1, "name": "Maple Court", "address": "18 Maple Street", "unit_count": 24}]


class PropertyInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=5, max_length=240)
    unit_count: int = Field(ge=1, le=5000)


@router.get("")
def list_properties():
    return PROPERTIES


@router.post("", status_code=201)
def create_property(payload: PropertyInput):
    property_record = {"id": max((item["id"] for item in PROPERTIES), default=0) + 1, **payload.model_dump()}
    PROPERTIES.append(property_record)
    return property_record
