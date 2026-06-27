from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.shared.enums import CreditStatus, LoanStatus
from app.shared.schemas import ORMModel


class ExpenseCreate(BaseModel):
    farm_id: uuid.UUID | None = None
    crop_cycle_id: uuid.UUID | None = None
    livestock_id: uuid.UUID | None = None
    category: str = "general"
    amount: float = Field(gt=0)
    currency: str = "USD"
    txn_date: date | None = None
    description: str | None = None


class ExpenseUpdate(BaseModel):
    category: str | None = None
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = None
    txn_date: date | None = None
    description: str | None = None
    farm_id: uuid.UUID | None = None


class ExpenseOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    farm_id: uuid.UUID | None
    crop_cycle_id: uuid.UUID | None
    livestock_id: uuid.UUID | None
    category: str
    amount: float
    currency: str
    txn_date: date | None
    description: str | None
    created_at: datetime


class IncomeCreate(BaseModel):
    farm_id: uuid.UUID | None = None
    crop_cycle_id: uuid.UUID | None = None
    livestock_id: uuid.UUID | None = None
    source: str = "sales"
    amount: float = Field(gt=0)
    currency: str = "USD"
    txn_date: date | None = None
    description: str | None = None


class IncomeUpdate(BaseModel):
    source: str | None = None
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = None
    txn_date: date | None = None
    description: str | None = None
    farm_id: uuid.UUID | None = None


class IncomeOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    farm_id: uuid.UUID | None
    source: str
    amount: float
    currency: str
    txn_date: date | None
    description: str | None
    created_at: datetime


class LoanCreate(BaseModel):
    lender: str
    principal: float = Field(gt=0)
    interest_rate: float = Field(default=0, ge=0)
    balance: float | None = None
    currency: str = "USD"
    disbursed_date: date | None = None
    due_date: date | None = None
    status: LoanStatus = LoanStatus.ACTIVE


class LoanUpdate(BaseModel):
    lender: str | None = None
    principal: float | None = Field(default=None, gt=0)
    interest_rate: float | None = Field(default=None, ge=0)
    balance: float | None = Field(default=None, ge=0)
    due_date: date | None = None
    status: LoanStatus | None = None


class LoanOut(ORMModel):
    id: uuid.UUID
    lender: str
    principal: float
    interest_rate: float
    balance: float
    currency: str
    disbursed_date: date | None
    due_date: date | None
    status: LoanStatus


class InputCreditCreate(BaseModel):
    provider: str
    item: str
    value: float = Field(gt=0)
    currency: str = "USD"
    issued_date: date | None = None
    repayment_due: date | None = None
    status: CreditStatus = CreditStatus.ISSUED


class InputCreditUpdate(BaseModel):
    provider: str | None = None
    item: str | None = None
    value: float | None = Field(default=None, gt=0)
    repayment_due: date | None = None
    status: CreditStatus | None = None


class InputCreditOut(ORMModel):
    id: uuid.UUID
    provider: str
    item: str
    value: float
    currency: str
    issued_date: date | None
    repayment_due: date | None
    status: CreditStatus


# ---- Reports ----
class CashflowPeriod(BaseModel):
    period: str  # YYYY-MM
    income: float
    expense: float
    net: float


class CashflowReport(BaseModel):
    currency: str
    periods: list[CashflowPeriod]
    total_income: float
    total_expense: float
    net: float


class ProfitabilityReport(BaseModel):
    currency: str
    total_income: float
    total_expense: float
    gross_profit: float
    margin_pct: float
    outstanding_loans: float
    outstanding_credit: float


class EnterpriseLine(BaseModel):
    enterprise: str
    income: float
    expense: float
    net: float


class EnterpriseAnalysis(BaseModel):
    currency: str
    lines: list[EnterpriseLine]
