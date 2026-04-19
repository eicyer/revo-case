from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    name: str
    hq: str
    website: str



class CompetitorOut(BaseModel):
    name: str
    summary: list[str]
    known_company_id: int | None = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    hq: str
    website: str
    status: str
    summary: list[str] | None
    competitors: list[CompetitorOut] | None
    error: str | None
    created_at: datetime