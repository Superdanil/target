import asyncio
import datetime
import os

import websockets

CHUNK_SIZE = 256  # в байтах


async def send_file(ws, file_path: str):
    """Отправка файла чанками по вебсокету."""
    file_size = os.path.getsize(file_path)
    print(f"📤 Отправляем файл: {file_path} ({file_size} байт)")

    with open(file_path, "rb") as f:
        chunk_index = 0
        while chunk := f.read(CHUNK_SIZE):
            await ws.send(chunk)
            chunk_index += 1
            print(f"📦 Отправлен chunk №{chunk_index} ({len(chunk)} байт)")

    await ws.send("EOF")  # End Of File
    print("✅ Отправка завершена.")


async def receive_responses(ws):
    """Получение mock-транскриптов от сервера"""
    try:
        async for message in ws:
            print(datetime.datetime.now(), f"🧠 Ответ сервера: ", message)
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Соединение закрыто сервером.")


async def main():
    uri = "ws://localhost:8000/ws"
    file_path = "strangers_in_the_night.txt"

    async with websockets.connect(uri, max_size=None) as ws:
        # Запускаем отправку и приём параллельно
        sender = asyncio.create_task(send_file(ws, file_path))
        receiver = asyncio.create_task(receive_responses(ws))

        await sender
        await receiver


if __name__ == "__main__":
    asyncio.run(main())
