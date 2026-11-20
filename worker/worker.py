import time

import requests

from renderer.mandelbrot import MandelbrotRenderer


class Worker:
    def __init__(self, worker_id, coordinator_url):
        self.id = worker_id
        self.coordinator_url = coordinator_url
        self.job = None
        self.renderer = None
        self.assigned_task = None
        self.attempt = None

    def request_task(self):
        response = requests.post(
            f"{self.coordinator_url}/tasks/request",
            json={"worker_id": self.id},
            timeout=10,
        )
        response.raise_for_status()
        assignment = response.json()
        self.assigned_task = assignment["task"]

        if self.assigned_task is not None:
            self.attempt = assignment["attempt"]
            job = assignment["job"]
            if job != self.job:
                self.job = job
                self.renderer = MandelbrotRenderer(job)

        return self.assigned_task

    def get_status(self):
        response = requests.get(
            f"{self.coordinator_url}/status",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def render(self):
        return self.renderer.render_tile(self.assigned_task)

    def submit_result(self, result):
        response = requests.post(
            f"{self.coordinator_url}/tasks/complete",
            json={
                "task_id": self.assigned_task["task_id"],
                "worker_id": self.id,
                "result": result,
                "attempt": self.attempt,
            },
            timeout=10,
        )
        response.raise_for_status()
        completion = response.json()
        return completion["accepted"]

    def run_once(self):
        task = self.request_task()

        if task is None:
            print("No task available right now")
            return

        result = self.render()

        if self.submit_result(result):
            print("Completed task", task["task_id"])
        else:
            print("The coordinator did not accept the result")

    def run(self):
        while True:
            task = self.request_task()

            if task is None:
                status = self.get_status()
                pending_count = status["PENDING"]["count"]
                running_count = status["RUNNING"]["count"]

                if pending_count == 0 and running_count == 0:
                    failed_count = status["FAILED"]["count"]
                    if failed_count > 0:
                        print(f"Job finished with {failed_count} failed tasks")
                    else:
                        print("All tasks completed")
                    return

                print("No task available right now")
                time.sleep(2)
                continue

            result = self.render()

            if self.submit_result(result):
                print("Completed task", task["task_id"])
            else:
                print(f"The coordinator did not accept the result from task {task['task_id']}")
