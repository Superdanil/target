import asyncio
from multiprocessing import Queue
from typing import Any

from logger import logger


class AudioProcessor:
    """Асинхронный обработчик, работающий в отдельном процессе."""

    def __init__(self, request_queue: Queue, response_queue: Queue, processing_time: float = 5.0):
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.processing_time = processing_time

    async def _process_once(self, message: dict) -> dict[str, Any]:
        """Асинхронная обработка одного аудио-сообщения."""
        client_id = message.get("client_id")
        audio = message.get("audio", b"")
        try:
            await asyncio.sleep(self.processing_time)  # имитация транскрипции

            text = audio.decode("utf-8", errors="ignore").strip().upper()

            result = {"client_id": client_id, "text": f"MOCK: {text}"}
            self.response_queue.put(result)
        except Exception as exc:
            # если ошибка, возвращаем сообщение об ошибке
            self.response_queue.put({"client_id": client_id, "error": True, "text": str(exc)})

    async def _read_queue(self):
        """
        Асинхронно читает blocking multiprocessing.Queue с помощью to_thread.
        Каждое сообщение отправляется в отдельную задачу (_process_once).
        """
        while True:
            message = await asyncio.to_thread(self.request_queue.get)
            if message is None:
                break

            asyncio.create_task(self._process_once(message))
            await asyncio.sleep(0.1)

    def run(self):
        """Точка входа для multiprocessing.Process. Запускает event loop и async-задачи внутри процесса."""
        logger.info("AudioProcessor процесс запущен")
        asyncio.run(self._read_queue())
