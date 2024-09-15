import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timedelta

from DB.db_control import (
    db_worker_register,
    db_matricular_proceso,
    db_healthcheaker_worker,
    db_actualizar_task,
    db_dashboard_workers,
    db_dashboard_process,
    db_dashboard_tasks,
    db_end_process,
    MAX_HEALTHCHECK,
)


app = FastAPI(title="Process monitor")


# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las URLs de origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)


# Example token for authentication
VALID_TOKEN = os.environ.get("TOKEN", "mysecrettoken")
VERSION = "v1.1"


def authenticate(authorization: Optional[str] = Header(None)):
    if authorization != f"Bearer {VALID_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


class Task(BaseModel):
    name: str
    version: str


class ProcessIn(BaseModel):
    name: str
    version: str
    tasks: List[Task]


class ProcessOut(BaseModel):
    id: str


class HealthCheckerIn(BaseModel):
    id: str


class DashboardTaskIn(BaseModel):
    id: str


class DashboardProcessIn(BaseModel):
    id: str


class HealthCheckerOut(BaseModel):
    health: int


class NewProcessIn(BaseModel):
    id: str


class EndProcessIn(BaseModel):
    id: str
    details: str = None


class EndProcessOut(BaseModel):
    status: bool


class NewProcessOut(BaseModel):
    father: str
    sons: List[dict]


class TaskUpdateIn(BaseModel):
    task_id: str
    status: str
    details: str = None


class TaskDetailOut(BaseModel):
    id: str
    name: str
    version: str
    state: str
    received: datetime
    started: Optional[datetime]
    runtime: timedelta
    father: str
    details: Optional[str]
    step: str


class ProcessDetailOut(BaseModel):
    id: str
    worker: str
    step: str
    status: str
    last_update: Optional[datetime]
    progress: str


class WorkerDetailOut(BaseModel):
    id: str
    status: str
    processed: int
    active: int
    successed: int
    failed: int
    load_average: str


@app.get("/version")
def read_root():
    return {"version": VERSION}


@app.post("/matricula", response_model=ProcessOut)
def api_worker_register(process: ProcessIn, auth: str = Depends(authenticate)):

    new_worker = process.dict()

    worker_id = db_worker_register(new_worker=new_worker)

    return {"id": worker_id}


@app.post("/healthchecker", response_model=HealthCheckerOut)
def api_healthcheaker_worker(
    request: HealthCheckerIn, auth: str = Depends(authenticate)
):
    worker_health = db_healthcheaker_worker(worker_id=request.id)

    return {
        "health": (
            worker_health < MAX_HEALTHCHECK
            if not isinstance(worker_health, str) > 8
            else 0
        )
    }


@app.post("/newprocess", response_model=NewProcessOut)
def api_new_process(request: NewProcessIn, auth: str = Depends(authenticate)):
    worker_id = request.id
    father_data = db_matricular_proceso(worker_id=worker_id)

    return father_data


#
@app.post("/endprocess", response_model=EndProcessOut)
def api_new_process(request: EndProcessIn, auth: str = Depends(authenticate)):
    process_id = request.id
    details = request.details
    status = db_end_process(process_id=process_id, details=details)

    return status


@app.post("/actualizar_task", response_model=dict)
def api_actualizar_task(request: TaskUpdateIn, auth: str = Depends(authenticate)):
    db_actualizar_task(request.task_id, request.status, request.details)

    return {"status": "ok"}


@app.get("/dashboard_tasks/{id}", response_model=List[TaskDetailOut])
def api_dashboard_tasks(id: str):
    return db_dashboard_tasks(id)


@app.get("/dashboard_process/{id}", response_model=List[ProcessDetailOut])
def api_dashboard_process(id: str):
    data = db_dashboard_process(id)

    # breakpoint()

    return data


@app.get("/dashboard_workers", response_model=List[WorkerDetailOut])
def api_dashboard_workers():
    return db_dashboard_workers()


# Ejecutar solo si el script es llamado directamente
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

    # gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8418 api:app
