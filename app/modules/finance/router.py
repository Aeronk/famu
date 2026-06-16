from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.finance.schemas import (
    CashflowReport,
    EnterpriseAnalysis,
    ExpenseCreate,
    ExpenseOut,
    IncomeCreate,
    IncomeOut,
    InputCreditCreate,
    InputCreditOut,
    LoanCreate,
    LoanOut,
    ProfitabilityReport,
)
from app.modules.finance.service import FinanceService
from app.shared.schemas import Page

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
