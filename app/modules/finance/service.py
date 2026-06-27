from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import Expense, Income, InputCredit, Loan
from app.modules.finance.repository import (
    ExpenseRepo,
    IncomeRepo,
    InputCreditRepo,
    LoanRepo,
)
from app.modules.finance.schemas import (
    CashflowPeriod,
    CashflowReport,
    EnterpriseAnalysis,
    EnterpriseLine,
    ExpenseCreate,
    IncomeCreate,
    InputCreditCreate,
    LoanCreate,
    ProfitabilityReport,
)
from app.shared.enums import CreditStatus, LoanStatus


class FinanceService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.tid = str(tenant_id)
        self.expenses = ExpenseRepo(session, tenant_id)
        self.incomes = IncomeRepo(session, tenant_id)
        self.loans = LoanRepo(session, tenant_id)
        self.credits = InputCreditRepo(session, tenant_id)

    # ---- transactions ----
    async def add_expense(self, data: ExpenseCreate) -> Expense:
        return await self.expenses.create(**data.model_dump())

    async def add_income(self, data: IncomeCreate) -> Income:
        return await self.incomes.create(**data.model_dump())

    async def add_loan(self, data: LoanCreate) -> Loan:
        payload = data.model_dump()
        if payload.get("balance") is None:
            payload["balance"] = payload["principal"]
        return await self.loans.create(**payload)

    async def add_credit(self, data: InputCreditCreate) -> InputCredit:
        return await self.credits.create(**data.model_dump())

    async def list_expenses(self, *, offset: int, limit: int):
        return await self.expenses.list(offset=offset, limit=limit), await self.expenses.count()

    async def list_incomes(self, *, offset: int, limit: int):
        return await self.incomes.list(offset=offset, limit=limit), await self.incomes.count()

    async def list_loans(self):
        return await self.loans.list(limit=500)

    async def list_credits(self):
        return await self.credits.list(limit=500)

    # ---- update / delete (full CRUD) ----
    async def update_expense(self, expense_id, data):
        obj = await self.expenses.get_or_404(expense_id)
        return await self.expenses.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_expense(self, expense_id):
        await self.expenses.delete(await self.expenses.get_or_404(expense_id))

    async def update_income(self, income_id, data):
        obj = await self.incomes.get_or_404(income_id)
        return await self.incomes.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_income(self, income_id):
        await self.incomes.delete(await self.incomes.get_or_404(income_id))

    async def update_loan(self, loan_id, data):
        obj = await self.loans.get_or_404(loan_id)
        return await self.loans.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_loan(self, loan_id):
        await self.loans.delete(await self.loans.get_or_404(loan_id))

    async def update_credit(self, credit_id, data):
        obj = await self.credits.get_or_404(credit_id)
        return await self.credits.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_credit(self, credit_id):
        await self.credits.delete(await self.credits.get_or_404(credit_id))

    # ---- reports ----
    async def _sum(self, model) -> float:
        stmt = select(func.coalesce(func.sum(model.amount), 0)).where(model.tenant_id == self.tid)
        return float((await self.session.execute(stmt)).scalar_one())

    async def cashflow(self, *, currency: str = "USD") -> CashflowReport:
        # Group by YYYY-MM in Python so the report is backend-portable
        # (avoids dialect-specific date formatting like to_char / strftime).
        def by_month(rows) -> dict[str, float]:
            out: dict[str, float] = {}
            for d, amount in rows:
                if d is None:
                    continue
                key = f"{d.year:04d}-{d.month:02d}"
                out[key] = out.get(key, 0.0) + float(amount)
            return out

        inc_rows = (
            await self.session.execute(
                select(Income.txn_date, Income.amount).where(
                    Income.tenant_id == self.tid, Income.txn_date.isnot(None)
                )
            )
        ).all()
        exp_rows = (
            await self.session.execute(
                select(Expense.txn_date, Expense.amount).where(
                    Expense.tenant_id == self.tid, Expense.txn_date.isnot(None)
                )
            )
        ).all()
        incomes = by_month(inc_rows)
        expenses = by_month(exp_rows)

        periods = sorted(set(incomes) | set(expenses))
        rows = [
            CashflowPeriod(
                period=p,
                income=round(incomes.get(p, 0.0), 2),
                expense=round(expenses.get(p, 0.0), 2),
                net=round(incomes.get(p, 0.0) - expenses.get(p, 0.0), 2),
            )
            for p in periods
        ]
        total_income = round(sum(r.income for r in rows), 2)
        total_expense = round(sum(r.expense for r in rows), 2)
        return CashflowReport(
            currency=currency,
            periods=rows,
            total_income=total_income,
            total_expense=total_expense,
            net=round(total_income - total_expense, 2),
        )

    async def profitability(self, *, currency: str = "USD") -> ProfitabilityReport:
        total_income = await self._sum(Income)
        total_expense = await self._sum(Expense)
        gross = round(total_income - total_expense, 2)

        loans = (
            await self.session.execute(
                select(func.coalesce(func.sum(Loan.balance), 0)).where(
                    Loan.tenant_id == self.tid, Loan.status == LoanStatus.ACTIVE
                )
            )
        ).scalar_one()
        credit = (
            await self.session.execute(
                select(func.coalesce(func.sum(InputCredit.value), 0)).where(
                    InputCredit.tenant_id == self.tid, InputCredit.status != CreditStatus.REPAID
                )
            )
        ).scalar_one()

        return ProfitabilityReport(
            currency=currency,
            total_income=round(total_income, 2),
            total_expense=round(total_expense, 2),
            gross_profit=gross,
            margin_pct=round((gross / total_income * 100) if total_income else 0.0, 2),
            outstanding_loans=round(float(loans), 2),
            outstanding_credit=round(float(credit), 2),
        )

    async def enterprise_analysis(self, *, currency: str = "USD") -> EnterpriseAnalysis:
        inc_stmt = (
            select(Income.source, func.coalesce(func.sum(Income.amount), 0))
            .where(Income.tenant_id == self.tid)
            .group_by(Income.source)
        )
        exp_stmt = (
            select(Expense.category, func.coalesce(func.sum(Expense.amount), 0))
            .where(Expense.tenant_id == self.tid)
            .group_by(Expense.category)
        )
        income_by = {k: float(v) for k, v in (await self.session.execute(inc_stmt)).all()}
        expense_by = {k: float(v) for k, v in (await self.session.execute(exp_stmt)).all()}

        merged: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for k, v in income_by.items():
            merged[k]["income"] += v
        for k, v in expense_by.items():
            merged[k]["expense"] += v

        lines = [
            EnterpriseLine(
                enterprise=name,
                income=round(vals["income"], 2),
                expense=round(vals["expense"], 2),
                net=round(vals["income"] - vals["expense"], 2),
            )
            for name, vals in sorted(merged.items())
        ]
        return EnterpriseAnalysis(currency=currency, lines=lines)
