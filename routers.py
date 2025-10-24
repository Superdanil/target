# routers/ws_router.py
import asyncio
import json
import uuid
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# ---------- WebSocket connection manager ----------
class WSManager:
    """Хранит активные websocket-соединения (client_id -> WebSocket)."""

    def __init__(self):
        self._conns: Dict[str, WebSocket] = {}
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


# ---------- Background task ----------
async def response_forwarder(response_queue, stop_event: asyncio.Event):
    """Слушает очередь и форвардит ответы клиентам."""
    print("🐇 response_forwarder started")
    while not stop_event.is_set():
        try:
            message = await asyncio.to_thread(response_queue.get)
            if message is None:
                break
            client_id = message.get("client_id")
            if client_id:
                await ws_manager.send(client_id, message)
        except Exception as e:
            print(f"⚠️ forwarder error: {e}")
            await asyncio.sleep(0.05)
    print("🐇 response_forwarder stopped")


# ---------- WebSocket endpoint ----------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Основной WebSocket endpoint для приёма аудио чанков и отправки транскриптов."""
    client_id = str(uuid.uuid4())
    await websocket.accept()
    await ws_manager.connect(client_id, websocket)
    print(f"🔌 Client connected: {client_id}")

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
                        print(f"📄 Text from {client_id}: {text}")

            elif msg["type"] == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(client_id)
        print(f"❌ Client disconnected: {client_id}")
