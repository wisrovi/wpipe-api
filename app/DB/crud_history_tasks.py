from DB.structure import HistoryTask, get_session


def create_history_task(
    uuid,
    name,
    status,
    order,
    version,
    create,
    started,
    update,
    father,
    details=None,
):
    with get_session() as db:
        try:
            nueva_tarea = HistoryTask(
                uuid=uuid,
                name=name,
                status=status,
                order=order,
                version=version,
                create=create,
                started=started,
                update=update,
                father=father,
                details=details,
            )
            db.add(nueva_tarea)
            db.commit()
            db.refresh(nueva_tarea)
            return nueva_tarea
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def get_history_tasks():
    with get_session() as db:
        try:
            return db.query(HistoryTask).all()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def get_history_tasks_by_father(father_id):
    with get_session() as db:
        try:
            return db.query(HistoryTask).filter_by(father=father_id).all()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def update_history_task(task_id, **kwargs):
    with get_session() as db:
        try:
            task = db.query(HistoryTask).filter(HistoryTask.uuid == task_id).first()
            if task:
                for key, value in kwargs.items():
                    setattr(task, key, value)
                db.commit()
                db.refresh(task)
            return task
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def delete_history_task(task_id):
    with get_session() as db:
        try:
            task = db.query(HistoryTask).filter(HistoryTask.uuid == task_id).first()
            if task:
                db.delete(task)
                db.commit()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e
