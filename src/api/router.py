import logging
from contextlib import asynccontextmanager
from pylib_0xe.config.config import Config
from fastapi import APIRouter, FastAPI

from src.orchestrators.initialize import Initialize
from .company_router import router as company_router
from .chat_router import router as chatbot_router

version = Config.read("api.version")

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize
    LOGGER.info(f"in the lifespan of the main router")
    Initialize()
    yield
    # cleanup
    LOGGER.info(f"Cleanup")


router = APIRouter(
    prefix=f"/v{version}",
    lifespan=lifespan,
    responses={404: {"description": "Not found"}},
)

router.include_router(company_router)
router.include_router(chatbot_router)
