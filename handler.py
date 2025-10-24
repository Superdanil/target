import asyncio
import queue
import time
from concurrent.futures.thread import ThreadPoolExecutor


class AudioProcessor:

    def __init__(self, request_queue, response_queue) -> None:
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _handle_audio(self, message: dict) -> None:
        text: str = message.pop("audio").decode().upper()
        message["text"] = text
        time.sleep(5)
        self.response_queue.put(message)

    async def _listen_request_queue(self):
        print("🐇 Очередь запросов прослушивается")
        while True:
            try:
                message = await asyncio.to_thread(self.request_queue.get_nowait)
            except queue.Empty:
                continue
            print(f"➡ Получено из request_queue: {message}")
            # Запускаем обработку в отдельном потоке
            await asyncio.get_event_loop().run_in_executor(self.executor, self._handle_audio, message)

    async def start(self) -> None:
        print("🔧 Процесс обработки данных запущен.")
        await self._listen_request_queue()
