from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Property
from app.schemas import PropertyInput, PropertyRead

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyRead])
def list_properties(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(Property).order_by(Property.id)).all()


@router.post("", response_model=PropertyRead, status_code=201)
def create_property(payload: PropertyInput, db: Annotated[Session, Depends(get_db)]):
    property_record = Property(**payload.model_dump())
    db.add(property_record)
    db.commit()
    db.refresh(property_record)
    return property_record
