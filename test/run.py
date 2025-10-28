import asyncio
import datetime
import json
import os
import time
from asyncio import AbstractEventLoop
from multiprocessing import Process

import websockets

URI = "ws://localhost:8000/ws"


class WSClient:
    """Асинхронный клиент, работающий в отдельном процессе."""

    def __init__(self, uri: str, name: str, chunk_size: int = 4096) -> None:
        self.uri = uri
        self.name = name
        self.chunk_size = chunk_size  # в байтах

    async def _send_file(self, ws, file_path: str):
        """Отправка файла чанками по вебсокету."""
        file_size = os.path.getsize(file_path)
        print(f"[{self.name}]📤 Отправляем файл: {file_path} ({file_size} байт)")

        with open(file_path, "rb") as f:
            chunk_index = 0
            while chunk := f.read(self.chunk_size):
                await ws.send(chunk)
                chunk_index += 1
                print(f"[{self.name}]📦 Отправлен chunk №{chunk_index} ({len(chunk)} байт)")

        await ws.send("EOF")  # End Of File
        print(f"[{self.name}]✅ Отправка завершена.")

    async def _receive_responses(self, ws):
        """Получение mock-транскриптов от сервера."""
        try:
            async for message in ws:
                json_ = json.loads(message)
                print(f"[{self.name}]🧠 {datetime.datetime.now()} Ответ сервера:", json_["text"])
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.name}]🔌 Соединение закрыто сервером.")

    async def _run(self, file_path: str) -> None:
        """Подключение к вебсерверу. Запуск задач на отправку и получение данных."""
        async with websockets.connect(self.uri, max_size=None) as ws:
            # Запускаем отправку и приём параллельно
            sender = asyncio.create_task(self._send_file(ws, file_path))
            receiver = asyncio.create_task(self._receive_responses(ws))

            await sender
            await receiver

    def start(self, file_path: str):
        """Запуск асинхронного клиента."""
        loop: AbstractEventLoop = asyncio.get_event_loop()
        loop.run_until_complete(self._run(file_path))


if __name__ == "__main__":
    client1 = WSClient(URI, "CLIENT 1", 256)
    client2 = WSClient(URI, "CLIENT 2", 1024)

    clients = (client1, client2)
    files = ("strangers_in_the_night.txt", "my_way.txt")

    missions = zip(clients, files)

    for mission in missions:
        Process(target=mission[0].start, args=(mission[1],)).start()
        time.sleep(2)
