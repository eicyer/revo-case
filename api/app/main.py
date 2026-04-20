from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from app.db import engine, Base
from app import models  # noqa: F401
from app.auth import get_current_admin
from app.routers import auth as auth_router
from app.routers import companies as companies_router
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Revo Case API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(companies_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}

