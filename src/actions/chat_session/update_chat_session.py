from dataclasses import dataclass
from pylib_0xe.database.actions.release_session import ReleaseSession
from pylib_0xe.types.database_types import DatabaseTypes

from src.models.chat_session import ChatSession
from src.repositories.repository import Repository


@dataclass
class UpdateChatSession:
    session_id: str
    messages: str

    def update(self) -> ChatSession:
        chat_session, db_session = Repository(ChatSession).read_by_id(
            self.session_id, db_session_keep_alive=True
        )
        chat_session.messages = self.messages
        db_session.commit()
        ReleaseSession(DatabaseTypes.I, db_session).release()
        return chat_session
