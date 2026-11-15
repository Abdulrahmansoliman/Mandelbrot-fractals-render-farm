import socket
import time
from multiprocessing import Process

import requests
import uvicorn

from worker.worker_manager import WorkerManager


def run_coordinator(listener):
    config = uvicorn.Config("coordinator.server:app", log_level="warning")
    server = uvicorn.Server(config)
    server.run(sockets=[listener])


def wait_for_coordinator(coordinator, coordinator_url):
    deadline = time.monotonic() + 15

    while time.monotonic() < deadline:
        if not coordinator.is_alive():
            raise RuntimeError("The coordinator stopped during startup")

        try:
            response = requests.get(f"{coordinator_url}/status", timeout=1)
            response.raise_for_status()
            return
        except requests.RequestException:
            time.sleep(0.1)

    raise RuntimeError("The coordinator did not become ready")


def main(worker_count=3, host="127.0.0.1", port=8000):
    with socket.socket() as listener:
        listener.bind((host, port))
        coordinator_url = f"http://{host}:{listener.getsockname()[1]}"
        manager = WorkerManager(worker_count, coordinator_url)
        coordinator = Process(target=run_coordinator, args=(listener,), name="coordinator")

        try:
            coordinator.start()
            wait_for_coordinator(coordinator, coordinator_url)
            print(f"Coordinator ready at {coordinator_url} (PID {coordinator.pid})", flush=True)
            manager.run()
        finally:
            if coordinator.is_alive():
                coordinator.terminate()
            if coordinator.pid is not None:
                coordinator.join()


if __name__ == "__main__":
    try:
        main(worker_count=3, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("Render farm stopped")
