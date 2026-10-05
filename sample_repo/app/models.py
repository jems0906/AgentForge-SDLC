from datetime import date

from app.database import Base
from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(240), nullable=False)
    unit_count: Mapped[int] = mapped_column(Integer, nullable=False)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(240), nullable=False)


class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_rent: Mapped[int] = mapped_column(Integer, nullable=False)


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)


class RentPayment(Base):
    __tablename__ = "rent_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lease_id: Mapped[int] = mapped_column(ForeignKey("leases.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
