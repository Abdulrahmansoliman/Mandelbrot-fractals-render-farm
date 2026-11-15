from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from protocols.single_coordinator import SingleCoordinator
from task.errors import InvalidResultError, TaskNotFoundError


def expect_error(error_type, method, *args):
    try:
        method(*args)
    except error_type:
        pass
    else:
        raise AssertionError(f"Expected {error_type.__name__}")


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
other_protocol = SingleCoordinator(job)
assert protocol.get_status()["PENDING"] == {"count": 2, "tasks": [0, 1]}
barrier = Barrier(8)


def request_together(index):
    barrier.wait(timeout=5)
    return protocol.request_task("worker_1")


with ThreadPoolExecutor(max_workers=8) as pool:
    assignments = list(pool.map(request_together, range(8)))

assert all(assignment["task"]["task_id"] == 0 for assignment in assignments)
assert sum(assignment["status"] == "assigned" for assignment in assignments) == 1
assert sum(assignment["status"] == "already_assigned" for assignment in assignments) == 7
assert protocol.queue.tasks[0]["attempts"] == 1
assert protocol.get_status()["PENDING"] == {"count": 1, "tasks": [1]}
assert other_protocol.get_status()["PENDING"] == {"count": 2, "tasks": [0, 1]}

assignment = protocol.request_task("worker_2")
assert assignment["task"]["task_id"] == 1
assert assignment["job"] == job
assert protocol.request_task("worker_3") == {"task": None}
assert protocol.request_task("worker_1")["status"] == "already_assigned"

result = [[None, 2], [3, 4]]
expect_error(TaskNotFoundError, protocol.complete_task, 99, "worker_1", result)
expect_error(InvalidResultError, protocol.complete_task, 0, "worker_1", [])
expect_error(InvalidResultError, protocol.complete_task, 0, "worker_1", [[1, 2], [3]])
assert protocol.get_status()["RUNNING"]["count"] == 2
assert protocol.complete_task(0, "wrong_worker", result) is False
assert protocol.complete_task(0, "worker_1", result) is True
assert protocol.complete_task(0, "worker_1", [[9, 9], [9, 9]]) is False
assert protocol.queue.tasks[0]["result"] == result
assert protocol.complete_task(1, "worker_2", result) is True
assert protocol.get_status() == {
    "PENDING": {"count": 0, "tasks": []},
    "RUNNING": {"count": 0, "tasks": []},
    "COMPLETED": {"count": 2, "tasks": [0, 1]},
    "FAILED": {"count": 0, "tasks": []},
}
assert other_protocol.get_status()["COMPLETED"]["count"] == 0

print("All SingleCoordinator tests passed!")
