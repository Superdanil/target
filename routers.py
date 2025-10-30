import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from logger import logger
from ws_manager import ws_manager

router = APIRouter()


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
