import asyncio
from contextlib import asynccontextmanager
from multiprocessing import Queue

from fastapi import FastAPI

from logger import logger
from ws_manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(response_forwarder(app.state.response_queue))
    yield


async def response_forwarder(response_queue: Queue):
    """Слушает очередь и форвардит ответы клиентам."""
    while True:
        try:
            message = await asyncio.to_thread(response_queue.get)
            if message is None:
                break
            client_id = message.get("client_id")
            if client_id:
                await ws_manager.send(client_id, message)
        except Exception as exc:
            logger.error("Ошибка в response_queue: %s", exc)
            await asyncio.sleep(0.05)
