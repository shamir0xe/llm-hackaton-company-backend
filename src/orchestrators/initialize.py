from pylib_0xe.database.mediators.engine_mediator import EngineMediator
from pylib_0xe.types.database_types import DatabaseTypes

from src.database.database_engine import DatabaseEngine


class Initialize:
    def __init__(self) -> None:
        EngineMediator().register(DatabaseTypes.I, DatabaseEngine().engine)
