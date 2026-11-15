import socket
import threading
import time
from contextlib import contextmanager

import requests
import uvicorn

from coordinator.server import create_app
from protocols.single_coordinator import SingleCoordinator


@contextmanager
def running_server(protocol):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        config = uvicorn.Config(create_app(protocol), log_level="error")
        server = uvicorn.Server(config)
        thread = threading.Thread(
            target=server.run,
            kwargs={"sockets": [listener]},
            daemon=True,
        )
        thread.start()

        try:
            deadline = time.monotonic() + 10
            while not server.started and time.monotonic() < deadline:
                assert thread.is_alive(), "Test server stopped during startup"
                time.sleep(0.05)
            assert server.started, "Test server did not start"
            yield url
        finally:
            server.should_exit = True
            thread.join(timeout=5)
            assert not thread.is_alive(), "Test server did not stop"


job = {
    "width": 4,
    "height": 2,
    "real_min": -2.0,
    "real_max": 1.0,
    "imag_min": -1.0,
    "imag_max": 1.0,
    "max_iterations": 10,
    "tile_size": 2,
}

protocol = SingleCoordinator(job)

with running_server(protocol) as url, requests.Session() as client:
    client.trust_env = False

    def post(path, body):
        return client.post(f"{url}{path}", json=body, timeout=3)

    response = client.get(f"{url}/status", timeout=3)
    assert response.status_code == 200
    assert response.json()["PENDING"] == {"count": 2, "tasks": [0, 1]}
    assert post("/tasks/request", {}).status_code == 422

    response = post("/tasks/request", {"worker_id": "worker_1"})
    assert response.status_code == 200
    assignment = response.json()
    assert assignment["status"] == "assigned"
    assert assignment["task"]["task_id"] == 0
    assert assignment["job"] == job

    response = post("/tasks/request", {"worker_id": "worker_2"})
    assert response.json()["task"]["task_id"] == 1
    assert post("/tasks/request", {"worker_id": "worker_3"}).json() == {"task": None}

    response = post("/tasks/request", {"worker_id": "worker_1"})
    assert response.json() == dict(assignment, status="already_assigned")

    completion = {
        "task_id": 0,
        "worker_id": "worker_1",
        "result": [[None, 2], [3, 4]],
    }

    response = post("/tasks/complete", dict(completion, task_id=99))
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}

    for result, detail in [
        ([], "Expected 2 rows"),
        ([[1, 2], [3]], "Each row must contain 2 values"),
    ]:
        response = post("/tasks/complete", dict(completion, result=result))
        assert response.status_code == 422
        assert response.json() == {"detail": detail}

    assert post("/tasks/complete", dict(completion, result="invalid")).status_code == 422
    response = post("/tasks/complete", dict(completion, worker_id="wrong_worker"))
    assert response.status_code == 200
    assert response.json() == {"accepted": False}

    response = post("/tasks/complete", completion)
    assert response.status_code == 200
    assert response.json() == {"accepted": True}
    assert post("/tasks/complete", completion).json() == {"accepted": False}
    response = post("/tasks/complete", dict(completion, task_id=1, worker_id="worker_2"))
    assert response.json() == {"accepted": True}

    assert post("/tasks/request", {"worker_id": "worker_1"}).json() == {"task": None}
    response = client.get(f"{url}/status", timeout=3)
    assert response.json() == {
        "PENDING": {"count": 0, "tasks": []},
        "RUNNING": {"count": 0, "tasks": []},
        "COMPLETED": {"count": 2, "tasks": [0, 1]},
        "FAILED": {"count": 0, "tasks": []},
    }

print("All HTTP server tests passed!")
