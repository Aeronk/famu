from __future__ import annotations

from app.modules.finance.models import Expense, Income, InputCredit, Loan
from app.tenancy.repository import TenantRepository


class ExpenseRepo(TenantRepository[Expense]):
    model = Expense


class IncomeRepo(TenantRepository[Income]):
    model = Income


class LoanRepo(TenantRepository[Loan]):
    model = Loan


class InputCreditRepo(TenantRepository[InputCredit]):
    model = InputCredit
