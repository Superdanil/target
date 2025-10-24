import asyncio
from contextlib import asynccontextmanager
from multiprocessing import Process, Queue

import uvicorn
from fastapi import FastAPI

from audio_processor import AudioProcessor
from routers import router as ws_router, response_forwarder


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state._response_task = asyncio.create_task(response_forwarder(app.state.response_queue))
    yield


def create_app(request_queue, response_queue, audio_proc):
    app = FastAPI(title="WS server", lifespan=lifespan)
    app.include_router(ws_router)
    app.state.request_queue = request_queue
    app.state.response_queue = response_queue
    app.state.audio_process = audio_proc
    return app


def run_audio_process(request_queue: Queue, response_queue: Queue) -> None:
    proc = AudioProcessor(request_queue, response_queue, processing_time=5)
    proc.run()


def main() -> None:
    request_queue: Queue = Queue()
    response_queue: Queue = Queue()

    audio_proc = Process(target=run_audio_process, args=(request_queue, response_queue), daemon=True)
    audio_proc.start()

    app = create_app(request_queue, response_queue, audio_proc)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
