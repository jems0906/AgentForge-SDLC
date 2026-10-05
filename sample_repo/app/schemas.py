from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PropertyInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=5, max_length=240)
    unit_count: int = Field(ge=1, le=5000)


class PropertyRead(PropertyInput, ReadModel):
    id: int


class TenantInput(BaseModel):
    property_id: int = Field(ge=1)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=240)


class TenantRead(TenantInput, ReadModel):
    id: int


class LeaseInput(BaseModel):
    tenant_id: int = Field(ge=1)
    starts_on: date
    ends_on: date
    monthly_rent: int = Field(gt=0)


class LeaseRead(LeaseInput, ReadModel):
    id: int


class TicketInput(BaseModel):
    property_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=180)
    priority: str = "normal"


class TicketRead(TicketInput, ReadModel):
    id: int
    status: str


class PaymentInput(BaseModel):
    lease_id: int = Field(ge=1)
    amount: int = Field(gt=0)


class PaymentRead(PaymentInput, ReadModel):
    id: int
    status: str
