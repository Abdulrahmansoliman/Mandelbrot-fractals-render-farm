from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from task.task import Task
from tile_generator.tile_generator import TileGenerator


app = FastAPI()

job = {
    "width": 800,
    "height": 600,
    "real_min": -2.0,
    "real_max": 1.0,
    "imag_min": -1.125,
    "imag_max": 1.125,
    "max_iterations": 100,
    "tile_size": 100
}

image = TileGenerator(job)

tiles = image.generate_tiles()

queue = Task(3)

queue.add_task(tiles)

queue_lock = Lock()


@app.get("/status")
def get_status():
    
    with queue_lock:
        summary = {
            "PENDING": {"count": 0, "tasks": []},
            "RUNNING": {"count": 0, "tasks": []},
            "COMPLETED": {"count": 0, "tasks": []},
            "FAILED": {"count": 0, "tasks": []}
        }
        
        for task_id, record in queue.tasks.items():
            status = record["status"]
            summary[status]["count"]+=1
            summary[status]["tasks"].append(task_id)
        
    return summary


class TaskRequest(BaseModel):
    worker_id: str


class CompletionRequest(BaseModel):
    task_id: int
    worker_id: str
    result: list[list[int | None]]


@app.post("/tasks/request")
def request_task(request: TaskRequest):

    with queue_lock:
        task = queue.get_worker_task(request.worker_id)
        status = "already_assigned"

        if task is None:
            if not queue.pending:
                return {"task": None}
            task = queue.assign_task(request.worker_id)
            status = "assigned"

        return {
            "status": status,
            "task": task,
            "job": job
        }


@app.post("/tasks/complete")
def complete_task(request: CompletionRequest):

    with queue_lock:
        record = queue.tasks.get(request.task_id)

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        task = record["task"]
        expected_rows = task["row_end"] - task["row_start"]
        expected_cols = task["col_end"] - task["col_start"]

        if len(request.result) != expected_rows:
            raise HTTPException(
                status_code=422,
                detail=f"Expected {expected_rows} rows",
            )

        for row in request.result:
            if len(row) != expected_cols:
                raise HTTPException(
                    status_code=422,
                    detail=f"Each row must contain {expected_cols} values",
                )

        accepted = queue.complete_task(
            request.task_id,
            request.worker_id,
            request.result,
        )

        return {"accepted": accepted}            
        


