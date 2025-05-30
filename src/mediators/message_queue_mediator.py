import asyncio
from typing import Dict
from pylib_0xe.decorators.singleton import singleton


@singleton
class MessageQueueMediator:
    def __init__(self) -> None:
        self.mq: Dict[str, asyncio.Queue] = {}

    async def get(self, key: str):
        if key in self.mq:
            return await self.mq[key].get()
        return None

    async def put(self, key: str, content: str):
        if key in self.mq:
            await self.mq[key].put(content)
