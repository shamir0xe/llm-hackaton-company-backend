import asyncio
from contextlib import asynccontextmanager
from fastapi import APIRouter, Body, FastAPI
from sse_starlette.sse import EventSourceResponse
from src.mediators.message_queue_mediator import MessageQueueMediator
from src.actions.chat_session.update_chat_session import UpdateChatSession
from src.orchestrators.agent_orchestrator import AgentOrchestrator
from src.models.chat_session import ChatSession
from src.repositories.repository import Repository
from src.types.api.masked_chat_session import MaskedChatSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize
    AgentOrchestrator()
    yield
    # cleanup


router = APIRouter(
    prefix=f"/chat",
    tags=["chat"],
    lifespan=lifespan,
)


@router.get("/create")
async def create() -> MaskedChatSession:
    chat_session, _ = Repository(ChatSession).create(ChatSession())
    asyncio.create_task(
        AgentOrchestrator().dispatch_greetings(session_id=chat_session.id)
    )
    return MaskedChatSession(**chat_session.to_dict())


@router.post("/update/{session_id}")
async def update(session_id: str, messages: str = Body(...)) -> MaskedChatSession:
    return MaskedChatSession(
        **UpdateChatSession(session_id, messages).update().to_dict()
    )


@router.get("/read/{session_id}")
async def read_chat(session_id: str) -> MaskedChatSession:
    chat_session, _ = Repository(ChatSession).read_by_id(session_id)
    return MaskedChatSession(**chat_session.to_dict())


@router.post("/update/{session_id}/user-message")
async def user_message(session_id: str, message: str = Body(...)) -> str:
    asyncio.create_task(
        AgentOrchestrator().dispatch_query(session_id=session_id, user_message=message)
    )
    return message


@router.get("/events/{session_id}")
async def sse(session_id: str):
    queue = asyncio.Queue()
    MessageQueueMediator().mq[session_id] = queue

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                if data == "FINISHED":
                    raise asyncio.CancelledError()
                yield {"event": "message", "data": data}
        except asyncio.CancelledError:
            del MessageQueueMediator().mq[session_id]
            raise

    return EventSourceResponse(event_generator())
