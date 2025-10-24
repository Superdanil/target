import asyncio
import json
import queue
import socket
from asyncio import AbstractEventLoop


class WebServer:
    def __init__(self, request_queue, response_queue) -> None:
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.client_sessions: dict[tuple[str, int], dict] = {}

    async def _send_response(self, connection: socket, loop: AbstractEventLoop):
        print("🐇 Очередь ответов прослушивается")
        while True:
            try:
                message = await asyncio.to_thread(self.response_queue.get_nowait)
            except queue.Empty:
                continue
            print(f"➡ Получено из response_queue: {message}")
            if message["error"]:
                message["text"] = "Ошибка обработки данных"
            await loop.sock_sendall(connection, message["text"].encode("utf-8"))
            print("Отправил ", message["text"].encode("utf-8"))

    async def _receive_audio(self, connection: socket, loop: AbstractEventLoop) -> None:
        address = connection.getpeername()
        try:
            while audio := await loop.sock_recv(connection, 2):
                print("Получены данные: ", audio)
                message = {"error": False, "address": address, "audio": audio}
                await asyncio.to_thread(self.request_queue.put, message)
                print("request_queue.qsize() =", self.request_queue.qsize())
        except Exception as exc:
            print(exc)

    async def _handle_client(self, connection: socket, loop: AbstractEventLoop):
        """Запуск приёма и отправки данных для одного клиента."""
        recv_task = asyncio.create_task(self._receive_audio(connection, loop))
        send_task = asyncio.create_task(self._send_response(connection, loop))

        done, pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Отменяем оставшуюся задачу
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Закрываем сокет только после завершения всех задач
        address = connection.getpeername()
        connection.close()
        print(f"❌ Клиент {address} отключился полностью")

    async def _listen_for_connection(self, server_socket: socket, loop: AbstractEventLoop) -> None:
        print("📡 Сервер готов принимать подключения")
        while True:
            connection, address = await loop.sock_accept(server_socket)
            connection.setblocking(False)
            print(f"🔌 Получен запрос на подключение от {address}")
            asyncio.create_task(self._handle_client(connection, loop))

    async def start(self) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_address = ("127.0.0.1", 8000)
        server_socket.setblocking(False)
        server_socket.bind(server_address)
        server_socket.listen()

        await self._listen_for_connection(server_socket, asyncio.get_event_loop())
