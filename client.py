import json
import socket
import time


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ("127.0.0.1", 8000)
    # Подключаемся к серверу
    for i in range(3):
        try:
            print(f"📡 Подключаемся к {server_address[0]}:{server_address[1]}")
            client_socket.connect(server_address)
            print("✅ Успешно подключено")
            break
        except Exception as exc:
            print(f"❌ {exc}")
            if i == 2:
                print(f"🛑 Не удалось подключиться к {server_address[0]}:{server_address[1]}")
                return

    while True:
        try:
            # Отправляем сообщение
            message = input("🗣 Введите байты: ")
            client_socket.sendall(message.encode("utf-8"))
            start = time.monotonic()
            # Получаем ответ
            data = client_socket.recv(1024)
            end = time.monotonic()
            text: str = json.loads(data.decode("utf-8"))["text"]
            print(f"↘️ Получено: {text} за {end - start} сек")
        except KeyboardInterrupt:
            client_socket.close()
            print("\n🛑 Соединение закрыто")
            break
        except Exception as exc:
            print(f"❌ Ошибка: {type(exc)} {exc}")


if __name__ == "__main__":
    main()
