import logging
from dataclasses import dataclass
from typing import Generic, List, Optional, Tuple, Type, TypeVar
from sqlalchemy.orm import Session
from pylib_0xe.decorators.db_session import db_session
from pylib_0xe.types.database_types import DatabaseTypes
from src.types.exception_types import ExceptionTypes
from src.models.decorated_base import DecoratedBase
from src.repositories.base_repository import BaseRepository
from src.types.server_exception import ServerException

LOGGER = logging.getLogger(__name__)
T = TypeVar("T", bound=DecoratedBase)


@dataclass
class Repository(Generic[T], BaseRepository[T, str]):
    model: Type[T]

    @db_session(DatabaseTypes.I)
    def read_by_id(
        self, id: str, session: Optional[Session] = None, *args, **kwargs
    ) -> Tuple[T, Session]:
        """Read by ID operation"""
        if not session:
            raise ServerException(ExceptionTypes.DB_SESSION_NOT_FOUND)
        return session.query(self.model).filter(self.model.id == id).one(), session

    @db_session(DatabaseTypes.I)
    def read(
        self, session: Optional[Session] = None, *args, **kwargs
    ) -> Tuple[List[T], Session]:
        """Read operation"""
        if not session:
            raise ServerException(ExceptionTypes.DB_SESSION_NOT_FOUND)
        return session.query(self.model).all(), session

    @db_session(DatabaseTypes.I)
    def create(
        self, entity: T, session: Optional[Session] = None, *args, **kwargs
    ) -> Tuple[T, Session]:
        """Create operation"""
        if not session:
            raise ServerException(ExceptionTypes.DB_SESSION_NOT_FOUND)
        model = (
            session.query(self.model).filter((self.model.id == entity.id)).one_or_none()
        )
        if not model:
            LOGGER.info(f"??? {entity.id}")
            # model = self.model(**entity.to_dict(exclude={"updated_at", "created_at"}))
            session.add(entity)
            session.flush()
        else:
            LOGGER.info(model.to_dict())
            return model, session
        return entity, session

    @db_session(DatabaseTypes.I)
    def update(
        self, entity: T, session: Optional[Session] = None, *args, **kwargs
    ) -> Tuple[T, Session]:
        """Update operation"""
        if not session:
            raise ServerException(ExceptionTypes.DB_SESSION_NOT_FOUND)
        model = session.query(self.model).filter(self.model.id == entity.id).first()
        if not model:
            raise Exception(ExceptionTypes.ID_INVALID)
        for key, value in entity.to_dict(
            exclude={"updated_at", "created_at", "id"}
        ).items():
            setattr(model, key, value)
        session.flush()
        return model, session

    @db_session(DatabaseTypes.I)
    def delete(
        self, entity: T, session: Optional[Session] = None, *args, **kwargs
    ) -> Tuple[T, Session]:
        """Delete operation"""
        if not session:
            raise ServerException(ExceptionTypes.DB_SESSION_NOT_FOUND)
        session.delete(entity)
        session.flush()
        return entity, session
