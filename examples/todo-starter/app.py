"""Local todo application. Run with: python -m uvicorn app:app --port 8090."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from storage import TaskStore

ROOT = Path(__file__).resolve().parent


class NewTask(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def validate_title(cls, title):
        if not title.strip():
            raise ValueError("Enter a task title")
        return title.strip()


class TaskUpdate(BaseModel):
    completed: bool


def create_app(data_dir: Path | None = None):
    application = FastAPI(title="testTodoapp")
    store = TaskStore(data_dir if data_dir is not None else ROOT / "data")

    @application.get("/")
    def home():
        return FileResponse(ROOT / "index.html")

    @application.get("/api/tasks")
    def tasks():
        return store.list()

    @application.post("/api/tasks", status_code=201)
    def add_task(body: NewTask):
        return store.add(body.title)

    @application.patch("/api/tasks/{task_id}")
    def update_task(task_id: str, body: TaskUpdate):
        try:
            return store.complete(task_id, body.completed)
        except KeyError as exc:
            raise HTTPException(404, "Task not found") from exc

    @application.delete("/api/tasks/{task_id}", status_code=204)
    def delete_task(task_id: str):
        try:
            store.delete(task_id)
        except KeyError as exc:
            raise HTTPException(404, "Task not found") from exc
        return Response(status_code=204)

    return application


app = create_app()
