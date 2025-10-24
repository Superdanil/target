import asyncio
from multiprocessing import Process, Queue, freeze_support

from handler import AudioProcessor
from server import WebServer


def run_webserver(request_queue, response_queue) -> None:
    loop = asyncio.get_event_loop()
    webserver = WebServer(request_queue, response_queue)
    loop.run_until_complete(webserver.start())
    loop.close()


def run_audio_processor(request_queue, response_queue) -> None:
    loop = asyncio.get_event_loop()
    audio_processor = AudioProcessor(request_queue, response_queue)
    loop.run_until_complete(audio_processor.start())
    loop.close()


async def main() -> None:
    request_queue = Queue()
    response_queue = Queue()

    audio_process = Process(target=run_audio_processor, args=(request_queue, response_queue))
    webserver_process = Process(target=run_webserver, args=(request_queue, response_queue))

    audio_process.start()
    webserver_process.start()


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
