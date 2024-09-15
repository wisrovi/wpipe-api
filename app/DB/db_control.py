from datetime import datetime
from DB.structure import generate_datetime
from DB.crud_worker import create_worker, update_worker, get_worker_by_id, get_workers
from DB.crud_history_tasks import (
    create_history_task,
    update_history_task,
    get_history_tasks_by_father,
)
from DB.crud_process import create_process, get_process_by_worker, update_process
import uuid
from collections import Counter


MAX_HEALTHCHECK = 30
PERMIT_TASK_STATES = ["start", "error", "success"]


def db_worker_register(new_worker: dict):

    # se valida que existan las claves: ["name", "version", "tasks"] en new_worker
    assert all(
        [key in ["name", "version", "tasks"] for key in new_worker.keys()]
    ), "No se encuentra alguna clave de worker: " + ",".join(
        ["name", "version", "tasks"]
    )

    # se valida que en las tasks (listado), cada una tenga las claves:  ["name", "version"]
    assert all(
        [
            all([t in ["name", "version"] for t in task.keys()])
            for task in new_worker["tasks"]
        ]
    ), f"Las taks deben tener las claves: {', '.join(['name', 'version', 'tasks'])}, pero alguna tarea no tiene una o mas de esas claves"

    new_worker_id = "worker_" + str(uuid.uuid1())

    real_new_tasks = [
        {"name": taks["name"], "version": taks["version"], "order": task_id + 1}
        for task_id, taks in enumerate(new_worker["tasks"])
    ]

    datetime_created = generate_datetime()

    nuevo_worker = create_worker(
        id=new_worker_id,
        nombre=new_worker["name"],
        version=new_worker["version"],
        last_healthcheker=datetime_created,
        datetime=datetime_created,
        tasks=real_new_tasks,
    )

    return nuevo_worker.id


def db_healthcheaker_worker(worker_id):
    worker = update_worker(worker_id=worker_id, last_healthcheker=generate_datetime())

    if worker:
        worker_health = (generate_datetime() - worker.last_healthcheker).seconds

    return MAX_HEALTHCHECK > worker_health if worker else "error"


def db_end_process(process_id, details: str = None):
    process = update_process(
        process_id=process_id,
        finished=generate_datetime(),
        error=details,
        status="success" if len(details) < 5 else "error",
    )

    return {"status": True if process else False}


def db_matricular_proceso(worker_id):

    worker = get_worker_by_id(worker_id)
    if worker:
        tasks = worker.tasks

        new_process_id = "process_" + str(uuid.uuid4())

        nuevo_proceso = create_process(
            father=new_process_id,
            process=worker_id,
            created=generate_datetime(),
            finished=None,
            status="running",
        )

        tasks_ids = []
        for task in tasks:
            new_task_id = "task_" + str(uuid.uuid4())

            nueva_tarea = create_history_task(
                uuid=new_task_id,
                name=task["name"],
                status="pending",
                order=task["order"],
                version=task["version"],
                create=generate_datetime(),
                started=None,
                update=None,
                father=new_process_id,
            )

            tasks_ids.append({"name": task["name"], "id": nueva_tarea.uuid})

        return {"father": nuevo_proceso.father, "sons": tasks_ids}


def db_actualizar_task(task_id, new_status_task: str, details=None):

    assert (
        new_status_task in PERMIT_TASK_STATES
    ), "Estado de tarea no valido, solo son permitidos los estados : {', '.join(PERMIT_STATES)}"

    if new_status_task == "start":
        task = update_history_task(
            task_id=task_id,
            status="running",
            started=generate_datetime(),
            update=generate_datetime(),
        )
    else:
        task = update_history_task(
            task_id=task_id,
            status=new_status_task,
            update=generate_datetime(),
            details=details,
        )

    return task


def db_dashboard_tasks(father_id):
    tasks = get_history_tasks_by_father(father_id)

    tasks_dashboard = []

    for task in tasks:

        tasks_dashboard.append(
            {
                "id": task.uuid,
                "name": task.name,
                "version": task.version,
                "state": task.status,
                "received": task.create,
                "started": task.started,
                "runtime": (
                    task.create - task.update
                    if task.update
                    else generate_datetime() - task.create
                ),
                "father": task.father,
                "details": task.details,
                "step": f"{task.order}/{len(tasks)}",
                "order": f"{task.order}",
            }
        )

    return tasks_dashboard


def db_dashboard_process(worker_id: str):

    worker = get_worker_by_id(worker_id)

    assert worker, "Worker not found"

    process_dashboard = []
    process = get_process_by_worker(worker_id)

    if process:

        for p in process:

            tasks = get_history_tasks_by_father(p.father)
            tasks = [
                (task.name, task.order, task.status, task.update) for task in tasks
            ]
            tasks = sorted(tasks, key=lambda x: x[1])
            tasks_updated = [(task) for task in tasks if task[3]]
            tasks_finished = [task for task in tasks_updated if task[2] != "running"]

            last_task = (
                tasks[0]
                if len(tasks_updated) == 0
                else sorted(tasks_updated, key=lambda x: x[3], reverse=True)[0]
            )

            progress = 0
            if last_task[2] != "pending":
                if tasks_updated and not tasks_finished:
                    progress = 0.01
                else:
                    progress = len(tasks_finished) / len(tasks)

            process_dashboard.append(
                {
                    "id": p.father,
                    "worker": worker.nombre,
                    "step": last_task[0],
                    "status": last_task[2],
                    "last_update": last_task[3],
                    "progress": f"{int(progress*100)}%",
                }
            )

    return process_dashboard


def db_dashboard_workers():
    workers = get_workers()

    worker_dashboard = []

    for worker in workers:
        worker_health = generate_datetime() - worker.last_healthcheker
        worker_status = (
            "online" if worker_health.seconds < MAX_HEALTHCHECK else "ofline"
        )

        process = get_process_by_worker(worker.id)
        process_status = dict(Counter([p.status for p in process]))
        process_time = [(p.finished - p.created).seconds for p in process if p.finished]

        print(worker_status)

        worker_dashboard.append(
            {
                "id": worker.id,
                "status": worker_status,
                "processed": len(process),
                "active": process_status.get("running", 0),
                "successed": process_status.get("success", 0),
                "failed": process_status.get("error", 0),
                "load_average": (
                    "NA"
                    if len(process_time) == 0
                    else str(sum(process_time) / len(process_time))
                ),
            }
        )

    return worker_dashboard


if __name__ == "__main__":
    new_worker = {
        "name": "Proceso1",
        "version": "1.0",
        "tasks": [
            {"name": "tarea1", "version": "1.0"},
            {"name": "tarea2", "version": "1.0"},
            {"name": "tarea3", "version": "1.0"},
            {"name": "tarea4", "version": "1.0"},
        ],
    }

    # worker_id = matricular_worker(new_worker=new_worker)
    worker_id = "worker_4db12d26-6d59-11ef-bba4-00e93a51a4ff"
    # worker_id = 'worker_09021dca-6d5e-11ef-96a9-00e93a51a4ff'
    worker_health = db_healthcheaker_worker(worker_id)

    # father_data = matricular_proceso(worker_id)
    father_data = "process_624f10f5-e697-469d-8d59-ed4eee3cdd75"

    task_id_1 = "task_e96b872b-1aee-42ce-8092-849a5536ba05"
    task_id_2 = "task_75aff027-b737-48a9-b1f5-346b8266dd2c"
    task_id_3 = "task_6d2fffac-79d4-4acd-b0d7-f5b12f325fd0"
    task_id_4 = "task_8fbe3d4a-38fd-4410-9f99-d1caec127614"

    # actualizar_task(task_id_1, "start")
    # actualizar_task(task_id_1, "success")
    # actualizar_task(task_id_2, "start")

    print(worker_id)
    print(father_data)

    # worker_dashboard = dashboard_workers()
    worker_dashboard = [
        {
            "id": "worker_4db12d26-6d59-11ef-bba4-00e93a51a4ff",
            "status": "online",
            "processed": 1,
            "active": 1,
            "successed": 0,
            "failed": 0,
            "load average": "NA",
        },
        {
            "id": "worker_09021dca-6d5e-11ef-96a9-00e93a51a4ff",
            "status": "ofline",
            "processed": 0,
            "active": 0,
            "successed": 0,
            "failed": 0,
            "load average": "NA",
        },
    ]

    print(worker_dashboard)

    process_dashboard = db_dashboard_process(worker_id)
    process_dashboard = [
        {
            "id": "process_624f10f5-e697-469d-8d59-ed4eee3cdd75",
            "name": "Proceso1",
            "step": "tarea1",
            "status": "running",
            "last_update": datetime(2024, 9, 7, 23, 47, 47, 507393),
            "progress": 1,
        },
        {
            "id": "process_f143e339-295c-404a-9d91-3859cb45dda6",
            "name": "Proceso1",
            "step": "tarea1",
            "status": "pending",
            "last_update": None,
            "progress": 0,
        },
    ]

    print(process_dashboard)
    print()

    tasks_dashboard = db_dashboard_tasks(father_data)
    print(tasks_dashboard)
