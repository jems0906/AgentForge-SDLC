from dataclasses import dataclass
from datetime import date


@dataclass
class Property:
    id: int
    name: str
    address: str
    unit_count: int


@dataclass
class Tenant:
    id: int
    property_id: int
    name: str
    email: str


@dataclass
class Lease:
    id: int
    tenant_id: int
    starts_on: date
    ends_on: date
    monthly_rent: int


@dataclass
class MaintenanceTicket:
    id: int
    property_id: int
    title: str
    priority: str = "normal"
    status: str = "open"


@dataclass
class RentPayment:
    id: int
    lease_id: int
    amount: int
    status: str = "pending"
