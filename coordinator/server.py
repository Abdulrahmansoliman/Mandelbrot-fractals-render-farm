import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from task.errors import InvalidResultError, TaskNotFoundError


class TaskRequest(BaseModel):
    worker_id: str


class CompletionRequest(BaseModel):
    task_id: int
    worker_id: str
    result: list[list[int | None]]
    attempt: int


def create_app(protocol, worker_manager=None):
    async def check_timeouts():
        while True:
            protocol.expire_tasks()
            await asyncio.sleep(0.5)

    @asynccontextmanager
    async def lifespan(app):
        timeout_checker = asyncio.create_task(check_timeouts())
        try:
            if worker_manager is not None:
                worker_manager.start()
            yield
        finally:
            timeout_checker.cancel()
            with suppress(asyncio.CancelledError):
                await timeout_checker
            if worker_manager is not None:
                worker_manager.stop()

    app = FastAPI(lifespan=lifespan)

    @app.post("/workers/{worker_id}/kill")
    def kill_worker(worker_id: str):
        if worker_manager is None:
            raise HTTPException(status_code=503, detail="Worker manager is not available")
        try:
            killed = worker_manager.kill(worker_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {"worker_id": worker_id, "killed": killed}

    @app.post("/workers/{worker_id}/restart")
    def restart_worker(worker_id: str):
        if worker_manager is None:
            raise HTTPException(status_code=503, detail="Worker manager is not available")
        try:
            restarted = worker_manager.restart(worker_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {"worker_id": worker_id, "restarted": restarted}

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
                request.attempt,
            )
        except TaskNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except InvalidResultError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        return {"accepted": accepted}

    return app
