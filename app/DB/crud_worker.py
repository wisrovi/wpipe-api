from DB.structure import Worker, get_session


def create_worker(id, nombre, version, last_healthcheker, datetime, tasks):
    with get_session() as db:
        try:
            nuevo_worker = Worker(
                id=id,
                nombre=nombre,
                version=version,
                last_healthcheker=last_healthcheker,
                datetime=datetime,
                tasks=tasks,
            )
            db.add(nuevo_worker)
            db.commit()
            db.refresh(nuevo_worker)
            return nuevo_worker
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def get_workers():
    with get_session() as db:
        try:
            return db.query(Worker).all()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def get_worker_by_id(worker_id):
    with get_session() as db:
        try:
            return db.query(Worker).filter_by(id=worker_id).first()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def update_worker(worker_id, **kwargs):
    with get_session() as db:
        try:
            worker = db.query(Worker).filter(Worker.id == worker_id).first()
            if worker:
                for key, value in kwargs.items():
                    setattr(worker, key, value)
                db.commit()
                db.refresh(worker)
            return worker
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def delete_worker(worker_id):
    with get_session() as db:
        try:
            worker = db.query(Worker).filter(Worker.id == worker_id).first()
            if worker:
                db.delete(worker)
                db.commit()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e
