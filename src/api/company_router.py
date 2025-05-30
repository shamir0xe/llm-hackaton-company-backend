from contextlib import asynccontextmanager
from typing import List
from fastapi import APIRouter, Body, FastAPI

from src.actions.company.upsert_company import UpsertCompany
from src.models.company import Company
from src.repositories.repository import Repository
from src.types.api.masked_company import MaskedCompany


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize
    yield
    # cleanup


router = APIRouter(
    prefix=f"/company",
    tags=["company"],
    lifespan=lifespan,
)


@router.get("/read")
async def read() -> List[MaskedCompany]:
    companies, _ = Repository(Company).read()
    return [MaskedCompany(**company.to_dict()) for company in companies]


@router.post("/create")
async def upsert(session_id: str, data: str = Body(...)) -> MaskedCompany:
    return MaskedCompany(**UpsertCompany(session_id, data).upsert().to_dict())
