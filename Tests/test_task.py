from task.task import Task


# A small helper for calls that should reject invalid actions.
def expect_value_error(method, *args):
    try:
        method(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


first_tile = {
    "task_id": 0,
    "row_start": 0,
    "row_end": 10,
    "col_start": 0,
    "col_end": 10,
}

second_tile = {
    "task_id": 1,
    "row_start": 0,
    "row_end": 10,
    "col_start": 10,
    "col_end": 20,
}

queue = Task(max_attempts=2)

# Empty queues and unknown task IDs should raise ValueError.
expect_value_error(queue.peek_task)
expect_value_error(queue.assign_task, "worker_1")
expect_value_error(queue.complete_task, 99, "worker_1", [])
expect_value_error(queue.retry_task, 99)
expect_value_error(queue.fail_task, 99)

# New tasks start pending and unassigned, in the order they were added.
queue.add_task([first_tile, second_tile])
assert list(queue.pending) == [0, 1]

for tile in [first_tile, second_tile]:
    record = queue.tasks[tile["task_id"]]
    assert record["task"] == tile
    assert record["status"] == "PENDING"
    assert record["worker_id"] is None
    assert record["attempts"] == 0
    assert record["result"] is None

# Duplicate IDs should not overwrite the original task or add another entry.
expect_value_error(queue.add_task, [dict(first_tile, col_end=5)])
assert queue.tasks[0]["task"] == first_tile
assert len(queue.tasks) == 2
assert list(queue.pending) == [0, 1]

# Peeking should leave the task pending. Pending tasks cannot be finished or retried.
assert queue.peek_task() == first_tile
assert queue.peek_task() == first_tile
assert list(queue.pending) == [0, 1]
assert queue.complete_task(0, "worker_1", []) is False
assert queue.tasks[0]["status"] == "PENDING"
expect_value_error(queue.retry_task, 0)
expect_value_error(queue.fail_task, 0)

# Assignment takes the first pending tile and records its worker and attempt.
assert queue.assign_task("worker_1") == first_tile
assert queue.tasks[0]["status"] == "RUNNING"
assert queue.tasks[0]["worker_id"] == "worker_1"
assert queue.tasks[0]["attempts"] == 1
assert queue.peek_task() == second_tile

assert queue.assign_task("worker_2") == second_tile
assert list(queue.pending) == []
expect_value_error(queue.assign_task, "worker_3")

# Only the assigned worker can complete a running task.
result = [[3] * 10 for _ in range(10)]
assert queue.complete_task(0, "wrong_worker", result) is False
assert queue.tasks[0]["status"] == "RUNNING"
assert queue.tasks[0]["result"] is None

assert queue.complete_task(0, "worker_1", result) is True
assert queue.tasks[0]["status"] == "COMPLETED"
assert queue.tasks[0]["result"] == result
assert queue.tasks[0]["worker_id"] is None

# A repeated completion must not overwrite an accepted result.
assert queue.complete_task(0, "worker_1", [[99]]) is False
assert queue.tasks[0]["result"] == result
expect_value_error(queue.retry_task, 0)
expect_value_error(queue.fail_task, 0)

# Below the attempt limit, retrying puts unfinished work back into the queue.
assert queue.fail_task(1) is False
assert queue.tasks[1]["status"] == "RUNNING"
assert queue.dead == []

assert queue.retry_task(1) is True
assert queue.tasks[1]["status"] == "PENDING"
assert queue.tasks[1]["worker_id"] is None
assert queue.tasks[1]["attempts"] == 1
assert list(queue.pending) == [1]
expect_value_error(queue.retry_task, 1)
assert list(queue.pending) == [1]

# Reassignment starts another attempt; the previous worker can no longer finish it.
assert queue.assign_task("worker_3") == second_tile
assert queue.tasks[1]["status"] == "RUNNING"
assert queue.tasks[1]["worker_id"] == "worker_3"
assert queue.tasks[1]["attempts"] == 2
assert queue.complete_task(1, "worker_2", result) is False
assert queue.tasks[1]["status"] == "RUNNING"
assert queue.tasks[1]["result"] is None

# At the attempt limit, retrying marks the task failed instead of re-enqueueing it.
assert queue.retry_task(1) is True
assert queue.tasks[1]["status"] == "FAILED"
assert queue.tasks[1]["worker_id"] is None
assert queue.tasks[1]["result"] is None
assert queue.dead == [1]
assert list(queue.pending) == []
assert queue.complete_task(1, "worker_3", result) is False
expect_value_error(queue.retry_task, 1)
expect_value_error(queue.fail_task, 1)
assert queue.dead == [1]

print("All Task tests passed!")
