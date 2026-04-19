import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, func
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
    existing = await db.execute(
        select(Company).where(func.lower(Company.name) == body.name.lower())
    )
    company = existing.scalar_one_or_none()

    if company is None:
        # First time we've seen this company — insert
        company = Company(
            name=body.name,
            hq=body.hq,
            website=body.website,
            status="pending",
        )
        db.add(company)
    else:
        company.hq = body.hq
        company.website = body.website
        company.status = "pending"
        company.summary = None
        company.competitors = None
        company.error = None

    await db.commit()
    await db.refresh(company)

    background.add_task(_run_ai_task, company.id, company.name, company.hq, company.website)
    return CompanyOut.model_validate(company)



def _stamp_known_company_ids(companies: list[Company]) -> None:
    """Mutate each competitor dict in place to add `known_company_id`."""
    known = {c.name.lower(): c.id for c in companies}
    for company in companies:
        if not company.competitors:
            continue
        for comp in company.competitors:
            comp["known_company_id"] = known.get(comp["name"].lower())


@router.get("", response_model=list[CompanyOut])
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = list(result.scalars().all())
    _stamp_known_company_ids(companies)
    return [CompanyOut.model_validate(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    if company.competitors:
        # we can add index to postgres to make it faster
        competitor_names = [c["name"].lower() for c in company.competitors]
        result = await db.execute(
            select(Company.id, Company.name).where(
                func.lower(Company.name).in_(competitor_names)
            )
        )
        known = {name.lower(): id_ for id_, name in result.all()}
        for comp in company.competitors:
            comp["known_company_id"] = known.get(comp["name"].lower())

    return CompanyOut.model_validate(company)