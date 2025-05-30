import asyncio
from pylib_0xe.config.config import Config
from pylib_0xe.decorators.singleton import singleton
import logging

from src.mediators.message_queue_mediator import MessageQueueMediator
from src.actions.chat_session.update_chat_session import UpdateChatSession
from src.actions.company.upsert_company import UpsertCompany
from src.models.chat_session import ChatSession
from src.repositories.repository import Repository
from src.agents.agent_1 import Agent as Agent1

LOGGER = logging.getLogger(__name__)


@singleton
class AgentOrchestrator:
    def __init__(self) -> None:
        MessageQueueMediator()

    async def dispatch_query(self, session_id: str, user_message: str):
        chat_session, _ = Repository(ChatSession).read_by_id(session_id)
        agent = Agent1()
        response, _, built_data = agent.shot(chat_session.messages, user_message)
        LOGGER.info(f"response: {response}")
        UpdateChatSession(session_id, agent.history()).update()
        if built_data:
            LOGGER.info(f"going to save this data to DB: {built_data}")
            UpsertCompany(session_id, built_data).upsert()
        await MessageQueueMediator().put(session_id, response)

    async def dispatch_greetings(self, session_id: str):
        agent = Agent1()
        response = agent.get_initial_greeting()
        await asyncio.sleep(Config.read("main.greetings.sleep"))
        UpdateChatSession(session_id, agent.history()).update()
        await MessageQueueMediator().put(session_id, response)
