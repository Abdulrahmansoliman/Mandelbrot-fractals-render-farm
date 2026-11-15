from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, patch

from worker.worker import Worker


def make_status(pending=0, running=0, failed=0):
    return {
        "PENDING": {"count": pending},
        "RUNNING": {"count": running},
        "FAILED": {"count": failed},
    }


for unfinished_status in [make_status(pending=1), make_status(running=1)]:
    worker = Worker("worker_1", "http://unused")
    worker.request_task = Mock(side_effect=[None, {"task_id": 7}, None])
    worker.get_status = Mock(side_effect=[unfinished_status, make_status()])
    worker.render = Mock(return_value=[[3]])
    worker.submit_result = Mock(return_value=True)
    output = StringIO()

    with patch("worker.worker.time.sleep") as sleep, redirect_stdout(output):
        worker.run()

    sleep.assert_called_once_with(2)
    worker.render.assert_called_once_with()
    worker.submit_result.assert_called_once_with([[3]])
    assert worker.request_task.call_count == 3
    assert "Completed task 7" in output.getvalue()
    assert "All tasks completed" in output.getvalue()


for failed_count in [0, 2]:
    worker = Worker("worker_1", "http://unused")
    worker.request_task = Mock(side_effect=[None])
    worker.get_status = Mock(return_value=make_status(failed=failed_count))
    worker.render = Mock()
    worker.submit_result = Mock()
    output = StringIO()

    with patch("worker.worker.time.sleep") as sleep, redirect_stdout(output):
        worker.run()

    sleep.assert_not_called()
    worker.render.assert_not_called()
    worker.submit_result.assert_not_called()
    if failed_count:
        assert "Job finished with 2 failed tasks" in output.getvalue()
        assert "All tasks completed" not in output.getvalue()
    else:
        assert "All tasks completed" in output.getvalue()


worker = Worker("worker_1", "http://unused")
worker.request_task = Mock(side_effect=[{"task_id": 9}, None])
worker.get_status = Mock(return_value=make_status(failed=1))
worker.render = Mock(return_value=[[3]])
worker.submit_result = Mock(return_value=False)
output = StringIO()

with redirect_stdout(output):
    worker.run()

assert "The coordinator did not accept the result from task 9" in output.getvalue()
assert "Completed task 9" not in output.getvalue()

print("All Worker tests passed!")
