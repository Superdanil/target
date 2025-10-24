import asyncio
import json

from fastapi import WebSocket


class WSManager:
    """Хранит активные websocket-соединения (client_id -> WebSocket)."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()  # lock для работы с dict из разных тасок

    async def connect(self, client_id: str, websocket: WebSocket):
        async with self._lock:
            self._connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        async with self._lock:
            self._connections.pop(client_id, None)

    async def send(self, client_id: str, payload: dict) -> None:
        """Отправить json конкретному клиенту, если он все ещё подключен."""
        async with self._lock:
            ws = self._connections.get(client_id)
        if not ws:
            return
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            await self.disconnect(client_id)


ws_manager = WSManager()
