import socket

import uvicorn

from coordinator.server import create_app
from protocols.single_coordinator import SingleCoordinator
from worker.worker_manager import WorkerManager


job = {
    "width": 800,
    "height": 600,
    "real_min": -2.0,
    "real_max": 1.0,
    "imag_min": -1.125,
    "imag_max": 1.125,
    "max_iterations": 100,
    "tile_size": 100,
}


def main(
    worker_count=3,
    host="127.0.0.1",
    port=8000,
    protocol_class=SingleCoordinator,
    task_timeout=30,
):
    with socket.socket() as listener:
        listener.bind((host, port))
        listener.listen()
        coordinator_url = f"http://{host}:{listener.getsockname()[1]}"
        manager = WorkerManager(worker_count, coordinator_url)
        protocol = protocol_class(job, task_timeout=task_timeout)
        app = create_app(protocol, manager)
        server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
        print(f"Coordinator at {coordinator_url}. Press Ctrl+C to stop.", flush=True)
        server.run(sockets=[listener])


if __name__ == "__main__":
    try:
        main(
            worker_count=3,
            host="127.0.0.1",
            port=8000,
            protocol_class=SingleCoordinator,
            task_timeout=30,
        )
    except KeyboardInterrupt:
        print("Render farm stopped")
