from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import engine, Base
from app import models  # noqa: F401  


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Revo Case API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}