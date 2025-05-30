from typing import Optional, Tuple
from pylib_0xe.decorators.db_session import db_session
from pylib_0xe.types.database_types import DatabaseTypes
from sqlalchemy.orm import Session

from src.models.company import Company
from src.repositories.repository import Repository
from src.types.exception_types import ExceptionTypes


class CompanyRepository(Repository[Company]):
    @db_session(DatabaseTypes.I)
    def read_by_session_id(
        self, session_id: str, session: Optional[Session] = None
    ) -> Tuple[Company, Session]:
        if not session:
            raise Exception(ExceptionTypes.DB_SESSION_NOT_FOUND)
        entity = session.query(Company).filter(Company.session_id == session_id).one()
        return entity, session
