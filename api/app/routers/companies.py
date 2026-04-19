import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.db import SessionLocal
from app.deps import get_db
from app.models import Company
from app.schemas import CompanyCreate, CompanyOut
from app.ai import generate_company_intel


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
    dependencies=[Depends(get_current_admin)],
)


# ---- Background task ----

async def _run_ai_task(company_id: int, name: str, hq: str, website: str) -> None:
    """Open a fresh session, call Gemini, update the row."""
    async with SessionLocal() as db:
        company = await db.get(Company, company_id)
        if company is None:
            logger.error("Company %s vanished before AI task ran", company_id)
            return
        try:
            intel = await generate_company_intel(name, hq, website)
            company.summary = intel["summary"]
            company.competitors = intel["competitors"]
            company.status = "ready"
        except Exception as e:
            logger.exception("AI task failed for company %s", company_id)
            company.status = "failed"
            company.error = str(e)
        await db.commit()


# ---- Endpoint ----

@router.post("", response_model=CompanyOut, status_code=201)
async def create_company(
    body: CompanyCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    company = Company(
        name=body.name,
        hq=body.hq,
        website=body.website,
        status="pending",
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    background.add_task(_run_ai_task, company.id, company.name, company.hq, company.website)

    return CompanyOut.model_validate(company)