from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.finance.schemas import (
    CashflowReport,
    EnterpriseAnalysis,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    IncomeCreate,
    IncomeOut,
    IncomeUpdate,
    InputCreditCreate,
    InputCreditOut,
    InputCreditUpdate,
    LoanCreate,
    LoanOut,
    LoanUpdate,
    ProfitabilityReport,
)
from app.modules.finance.service import FinanceService
from app.shared.schemas import Message, Page

router = APIRouter(prefix="/finance", tags=["finance"])


# ---- transactions ----
@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("finance:create"))])
async def add_expense(payload: ExpenseCreate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).add_expense(payload)


@router.get("/expenses", response_model=Page[ExpenseOut], dependencies=[Depends(require_perm("finance:read"))])
async def list_expenses(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await FinanceService(session, tenant_id).list_expenses(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/incomes", response_model=IncomeOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("finance:create"))])
async def add_income(payload: IncomeCreate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).add_income(payload)


@router.get("/incomes", response_model=Page[IncomeOut], dependencies=[Depends(require_perm("finance:read"))])
async def list_incomes(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await FinanceService(session, tenant_id).list_incomes(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/loans", response_model=LoanOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("finance:create"))])
async def add_loan(payload: LoanCreate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).add_loan(payload)


@router.get("/loans", response_model=list[LoanOut], dependencies=[Depends(require_perm("finance:read"))])
async def list_loans(session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).list_loans()


@router.post("/input-credits", response_model=InputCreditOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("finance:create"))])
async def add_credit(payload: InputCreditCreate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).add_credit(payload)


@router.get("/input-credits", response_model=list[InputCreditOut], dependencies=[Depends(require_perm("finance:read"))])
async def list_credits(session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).list_credits()


# ---- update / delete (full CRUD) ----
@router.patch("/expenses/{expense_id}", response_model=ExpenseOut, dependencies=[Depends(require_perm("finance:update"))])
async def update_expense(expense_id: uuid.UUID, payload: ExpenseUpdate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).update_expense(expense_id, payload)


@router.delete("/expenses/{expense_id}", response_model=Message, dependencies=[Depends(require_perm("finance:delete"))])
async def delete_expense(expense_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await FinanceService(session, tenant_id).delete_expense(expense_id)
    return Message(message="Expense deleted")


@router.patch("/incomes/{income_id}", response_model=IncomeOut, dependencies=[Depends(require_perm("finance:update"))])
async def update_income(income_id: uuid.UUID, payload: IncomeUpdate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).update_income(income_id, payload)


@router.delete("/incomes/{income_id}", response_model=Message, dependencies=[Depends(require_perm("finance:delete"))])
async def delete_income(income_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await FinanceService(session, tenant_id).delete_income(income_id)
    return Message(message="Income deleted")


@router.patch("/loans/{loan_id}", response_model=LoanOut, dependencies=[Depends(require_perm("finance:update"))])
async def update_loan(loan_id: uuid.UUID, payload: LoanUpdate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).update_loan(loan_id, payload)


@router.delete("/loans/{loan_id}", response_model=Message, dependencies=[Depends(require_perm("finance:delete"))])
async def delete_loan(loan_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await FinanceService(session, tenant_id).delete_loan(loan_id)
    return Message(message="Loan deleted")


@router.patch("/input-credits/{credit_id}", response_model=InputCreditOut, dependencies=[Depends(require_perm("finance:update"))])
async def update_credit(credit_id: uuid.UUID, payload: InputCreditUpdate, session: DbSession, tenant_id: TenantId):
    return await FinanceService(session, tenant_id).update_credit(credit_id, payload)


@router.delete("/input-credits/{credit_id}", response_model=Message, dependencies=[Depends(require_perm("finance:delete"))])
async def delete_credit(credit_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await FinanceService(session, tenant_id).delete_credit(credit_id)
    return Message(message="Credit deleted")


# ---- reports ----
@router.get("/reports/cashflow", response_model=CashflowReport, dependencies=[Depends(require_perm("finance:read"))])
async def cashflow(session: DbSession, tenant_id: TenantId, currency: str = Query("USD")):
    return await FinanceService(session, tenant_id).cashflow(currency=currency)


@router.get("/reports/profitability", response_model=ProfitabilityReport, dependencies=[Depends(require_perm("finance:read"))])
async def profitability(session: DbSession, tenant_id: TenantId, currency: str = Query("USD")):
    return await FinanceService(session, tenant_id).profitability(currency=currency)


@router.get("/reports/enterprise", response_model=EnterpriseAnalysis, dependencies=[Depends(require_perm("finance:read"))])
async def enterprise(session: DbSession, tenant_id: TenantId, currency: str = Query("USD")):
    return await FinanceService(session, tenant_id).enterprise_analysis(currency=currency)
