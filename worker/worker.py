import requests

from renderer.mandelbrot import MandelbrotRenderer


class Worker:
    def __init__(self, job, task, w_id):
        self.id = w_id
        self.job = job
        self.renderer = MandelbrotRenderer(job)
        self.assigned_task = task

    def render(self):
        return self.renderer.render_tile(self.assigned_task)


def main(worker_id="worker_1", coordinator_url="http://127.0.0.1:8000"):
    response = requests.post(
        f"{coordinator_url}/tasks/request",
        json={"worker_id": worker_id},
        timeout=10,
    )
    response.raise_for_status()
    assignment = response.json()

    task = assignment["task"]

    if task is None:
        print("No task available right now")
        return

    worker = Worker(
        job=assignment["job"],
        task=task,
        w_id=worker_id,
    )

    result = worker.render()

    response = requests.post(
        f"{coordinator_url}/tasks/complete",
        json={
            "task_id": task["task_id"],
            "worker_id": worker_id,
            "result": result,
        },
        timeout=10,
    )
    response.raise_for_status()
    completion = response.json()

    if completion["accepted"]:
        print("Completed task", task["task_id"])
    else:
        print("The coordinator did not accept the result")


if __name__ == "__main__":
    main()
