from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from task.errors import InvalidResultError, TaskNotFoundError


class TaskRequest(BaseModel):
    worker_id: str


class CompletionRequest(BaseModel):
    task_id: int
    worker_id: str
    result: list[list[int | None]]


def create_app(protocol):
    app = FastAPI()

    @app.get("/status")
    def get_status():
        return protocol.get_status()

    @app.post("/tasks/request")
    def request_task(request: TaskRequest):
        return protocol.request_task(request.worker_id)

    @app.post("/tasks/complete")
    def complete_task(request: CompletionRequest):
        try:
            accepted = protocol.complete_task(
                request.task_id,
                request.worker_id,
                request.result,
            )
        except TaskNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except InvalidResultError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        return {"accepted": accepted}

    return app
