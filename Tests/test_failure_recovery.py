import socket
import threading
import time
from unittest.mock import patch

import requests
import uvicorn

from coordinator.server import create_app
from protocols.single_coordinator import SingleCoordinator
from worker.worker import Worker
from worker.worker_manager import WorkerManager


class SlowWorker(Worker):
    def run(self):
        if self.id != "worker_1":
            time.sleep(1)
        super().run()

    def render(self):
        if self.id == "worker_1":
            time.sleep(30)
        return super().render()


def test_recovery():
    job = {
        "width": 4, "height": 4, "tile_size": 2,
        "real_min": -2, "real_max": 1,
        "imag_min": -1, "imag_max": 1, "max_iterations": 10,
    }
    protocol = SingleCoordinator(job, task_timeout=3)
    with socket.socket() as listener, requests.Session() as client:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        client.trust_env = False
        manager = WorkerManager(3, url)
        server = uvicorn.Server(uvicorn.Config(create_app(protocol, manager), log_level="error"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]})
        with patch("worker.worker_manager.Worker", SlowWorker):
            thread.start()
            try:
                deadline = time.monotonic() + 15
                task_id = None
                while time.monotonic() < deadline:
                    with protocol.lock:
                        task = protocol.queue.get_worker_task("worker_1")
                        if task is not None:
                            task_id = task["task_id"]
                            break
                    time.sleep(0.05)
                assert task_id is not None, "Worker did not receive a task"
                response = client.post(f"{url}/workers/unknown/kill", timeout=3)
                assert response.status_code == 404
                assert all(process.is_alive() for process in manager.processes)
                response = client.post(f"{url}/workers/worker_1/kill", timeout=3)
                assert response.json() == {"worker_id": "worker_1", "killed": True}
                assert not manager.processes[0].is_alive()
                assert client.post(f"{url}/workers/worker_1/kill", timeout=3).json()["killed"] is False
                while time.monotonic() < deadline:
                    status = client.get(f"{url}/status", timeout=3).json()
                    if status["COMPLETED"]["count"] == 4:
                        break
                    time.sleep(0.1)
                assert status["COMPLETED"]["count"] == 4, status
                assert status["FAILED"]["count"] == 0
                assert protocol.queue.tasks[task_id]["attempts"] == 2
                manager.wait()
            finally:
                server.should_exit = True
                thread.join(timeout=10)
                assert not thread.is_alive()
                assert all(not process.is_alive() for process in manager.processes)
    print("Worker killed over HTTP; all tasks recovered and completed!")


if __name__ == "__main__":
    test_recovery()
