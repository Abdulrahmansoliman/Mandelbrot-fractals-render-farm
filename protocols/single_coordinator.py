from threading import Lock

from task.errors import InvalidResultError, TaskNotFoundError
from task.task import Task
from tile_generator.tile_generator import TileGenerator


class SingleCoordinator:
    def __init__(self, job, max_attempts=3):
        self.job = job.copy()
        self.queue = Task(max_attempts)
        self.queue.add_task(TileGenerator(self.job).generate_tiles())
        self.lock = Lock()

    def get_status(self):
        with self.lock:
            summary = {
                "PENDING": {"count": 0, "tasks": []},
                "RUNNING": {"count": 0, "tasks": []},
                "COMPLETED": {"count": 0, "tasks": []},
                "FAILED": {"count": 0, "tasks": []},
            }

            for task_id, record in self.queue.tasks.items():
                status = record["status"]
                summary[status]["count"] += 1
                summary[status]["tasks"].append(task_id)

            return summary

    def request_task(self, worker_id):
        with self.lock:
            task = self.queue.get_worker_task(worker_id)
            status = "already_assigned"

            if task is None:
                if not self.queue.pending:
                    return {"task": None}
                task = self.queue.assign_task(worker_id)
                status = "assigned"

            print("Worker", worker_id, "has task", task["task_id"], flush=True)

            return {
                "status": status,
                "task": task,
                "job": self.job,
            }

    def complete_task(self, task_id, worker_id, result):
        with self.lock:
            record = self.queue.tasks.get(task_id)

            if record is None:
                raise TaskNotFoundError("Task not found")

            task = record["task"]
            expected_rows = task["row_end"] - task["row_start"]
            expected_cols = task["col_end"] - task["col_start"]

            if len(result) != expected_rows:
                raise InvalidResultError(f"Expected {expected_rows} rows")

            for row in result:
                if len(row) != expected_cols:
                    raise InvalidResultError(
                        f"Each row must contain {expected_cols} values"
                    )

            return self.queue.complete_task(task_id, worker_id, result)
