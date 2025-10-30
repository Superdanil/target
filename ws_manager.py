import asyncio
import json

from fastapi.websockets import WebSocket

from logger import logger


class WSManager:
    """Хранит активные websocket-соединения (client_id -> WebSocket)."""

    def __init__(self) -> None:
        self._conns: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._conns[client_id] = websocket

    async def disconnect(self, client_id: str) -> None:
        async with self._lock:
            self._conns.pop(client_id, None)

    async def send(self, client_id: str, payload: dict) -> None:
        async with self._lock:
            ws = self._conns.get(client_id)
        if not ws:
            return
        try:
            await ws.send_json(payload)
        except Exception as exc:
            await self.disconnect(client_id)
            logger.error("Клиент отключился с ошибкой: %s", exc)


ws_manager = WSManager()
