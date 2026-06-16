from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID
from app.shared.enums import CreditStatus, LoanStatus, enum_type


class Expense(Base, TenantEntity):
    __tablename__ = "expenses"

    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    crop_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("crop_cycles.id", ondelete="SET NULL"), nullable=True
    )
    livestock_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(80), default="general", nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    txn_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Income(Base, TenantEntity):
    __tablename__ = "incomes"

    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    crop_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("crop_cycles.id", ondelete="SET NULL"), nullable=True
    )
    livestock_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(80), default="sales", nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    txn_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Loan(Base, TenantEntity):
    __tablename__ = "loans"

    lender: Mapped[str] = mapped_column(String(160), nullable=False)
    principal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    disbursed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[LoanStatus] = mapped_column(
        enum_type(LoanStatus), default=LoanStatus.ACTIVE, nullable=False
    )


class InputCredit(Base, TenantEntity):
    __tablename__ = "input_credits"

    provider: Mapped[str] = mapped_column(String(160), nullable=False)
    item: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    repayment_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[CreditStatus] = mapped_column(
        enum_type(CreditStatus), default=CreditStatus.ISSUED, nullable=False
    )
