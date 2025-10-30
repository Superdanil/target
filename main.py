from multiprocessing import Process, Queue

import uvicorn
from fastapi import FastAPI

from audio_processor import AudioProcessor
from lifespan import lifespan
from routers import router as ws_router


def create_app(request_queue: Queue, response_queue: Queue) -> FastAPI:
    app = FastAPI(title="WS server", lifespan=lifespan)
    app.include_router(ws_router)
    app.state.request_queue = request_queue
    app.state.response_queue = response_queue
    return app


def run_audio_process(request_queue: Queue, response_queue: Queue) -> None:
    proc = AudioProcessor(request_queue, response_queue, processing_time=5)
    proc.run()


def main() -> None:
    request_queue: Queue = Queue()
    response_queue: Queue = Queue()

    Process(target=run_audio_process, args=(request_queue, response_queue), daemon=True).start()

    app = create_app(request_queue, response_queue)

    uvicorn.run(app, host="127.0.0.1", port=8000, use_colors=True)


if __name__ == "__main__":
    main()
