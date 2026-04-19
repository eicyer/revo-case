import json
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings


class CompetitorIntel(BaseModel):
    name: str
    summary: list[str]


class CompanyIntel(BaseModel):
    summary: list[str]
    competitors: list[CompetitorIntel]


_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "array",
            "items": {"type": "string"},
        },
        "competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "summary": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["name", "summary"],
            },
        },
    },
    "required": ["summary", "competitors"],
}


_client = genai.Client(api_key=settings.GEMINI_API_KEY)


_PROMPT_TEMPLATE = """\
You are a market research assistant. Given a company, produce:
1. A short summary of the main company (4-5 short bullet points).
2. Exactly 5 competitors. For each, the company name and a short summary
   (4-5 short bullet points).

Bullets must be concise (one short sentence each), factual, and free of marketing fluff.

Company name: {name}
Headquarters: {hq}
Website: {website}
"""


async def generate_company_intel(name: str, hq: str, website: str) -> dict:
    """Call Gemini and return a dict matching CompanyIntel."""
    prompt = _PROMPT_TEMPLATE.format(name=name, hq=hq, website=website)

    response = await _client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_SCHEMA,
        ),
    )

    raw = json.loads(response.text)
    parsed = CompanyIntel.model_validate(raw)

    if len(parsed.competitors) != 5:
        raise ValueError(f"Expected 5 competitors, got {len(parsed.competitors)}")

    return parsed.model_dump()