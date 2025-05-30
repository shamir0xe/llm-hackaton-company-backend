import logging

import coloredlogs
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.types.server_exception import ServerException
from src.types.exception_types import ExceptionTypes
from src.api.router import router

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)

# Set logger
coloredlogs.install()
logging.basicConfig(level=logging.INFO)

# Create fastapi server
app = FastAPI(
    openapi_url="/api/openapi.json",  # Customize the OpenAPI schema URL
    docs_url="/api/docs",  # Customize the Swagger UI URL
)

# Configure CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServerException)
async def exception_handler(rq: Request, exc: ServerException):
    if exc.exception_type is ExceptionTypes.TOKEN_INVALID:
        return JSONResponse(status_code=401, content=exc.detail)
    return JSONResponse(
        status_code=418,
        content=exc.detail,
    )


app.include_router(router, prefix="/api")
