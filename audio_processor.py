import time
from multiprocessing import Queue


class AudioProcessor:
    """
    Работает в отдельном процессе. Блокирующе читает request_queue,
    делает mock-обработку и кладет результат в response_queue.
    """

    def __init__(self, request_queue: Queue, response_queue: Queue, processing_time: float = 5) -> None:
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.processing_time = processing_time

    def _process_once(self, message: dict):
        """
        Синхронная обработка одного сообщения.
        message: {"client_id": str, "audio": bytes}
        Положит в response_queue: {"client_id": str, "text": str}
        """
        client_id = message.get("client_id")
        audio = message.get("audio", b"")
        # mock-транскрипт: просто uppercase текста (без ошибок)
        try:
            text = audio.decode("utf-8", errors="ignore").upper()

            time.sleep(self.processing_time)  # имитация бурной деятельности

            result = {"client_id": client_id, "text": f"MOCK: {text}"}
            self.response_queue.put(result)
        except Exception as exc:
            # если ошибка, возвращаем сообщение об ошибке
            self.response_queue.put({"client_id": client_id, "error": True, "text": str(exc)})

    def run(self):
        print("🔧 AudioProcessor запущен", )
        while True:
            # блокирующий get: процесс просто ждёт задач
            message = self.request_queue.get()
            if message is None:
                break
            self._process_once(message)
        print("🔧 AudioProcessor остановлен")
