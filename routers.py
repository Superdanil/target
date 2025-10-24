import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from logger import logger

router = APIRouter()


class WSManager:
    """Хранит активные websocket-соединения (client_id -> WebSocket)."""

    def __init__(self):
        self._conns: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket):
        async with self._lock:
            self._conns[client_id] = websocket

    async def disconnect(self, client_id: str):
        async with self._lock:
            self._conns.pop(client_id, None)

    async def send(self, client_id: str, payload: dict):
        async with self._lock:
            ws = self._conns.get(client_id)
        if not ws:
            return
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            await self.disconnect(client_id)


ws_manager = WSManager()


async def response_forwarder(response_queue):
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


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Основной WebSocket endpoint для приёма аудио-чанков и отправки транскриптов."""
    client_id = str(uuid.uuid4())
    await websocket.accept()
    await ws_manager.connect(client_id, websocket)
    logger.info("Новый клиент: %s", client_id)

    app = websocket.app
    try:
        while True:
            msg = await websocket.receive()

            if msg["type"] == "websocket.receive":
                if "bytes" in msg:
                    data: bytes = msg["bytes"]
                    app.state.request_queue.put({"client_id": client_id, "audio": data})

                elif "text" in msg:
                    text = msg["text"]
                    if text == "EOF":
                        app.state.request_queue.put({"client_id": client_id, "audio": b"__EOF__"})
                    else:
                        logger.info("Текст от клиента %s: %s", client_id, text)

            elif msg["type"] == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(client_id)
        logger.info("Клиент отключился: %s", client_id)
