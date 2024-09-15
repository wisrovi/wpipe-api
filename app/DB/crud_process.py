from DB.structure import Process, get_session


def create_process(father, process, created, finished, status):
    with get_session() as db:
        try:
            nuevo_process = Process(
                father=father,
                process=process,
                created=created,
                finished=finished,
                status=status,
            )
            db.add(nuevo_process)
            db.commit()
            db.refresh(nuevo_process)
            return nuevo_process
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def get_processes():
    with get_session() as db:
        try:
            return db.query(Process).all()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def get_process_by_worker(worker_id):
    with get_session() as db:
        try:
            return db.query(Process).filter_by(process=worker_id).all()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def update_process(process_id, **kwargs):
    with get_session() as db:
        try:
            process = db.query(Process).filter(Process.father == process_id).first()
            if process:
                for key, value in kwargs.items():
                    setattr(process, key, value)
                db.commit()
                db.refresh(process)
            return process
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e


def delete_process(process_id):
    with get_session() as db:
        try:
            process = db.query(Process).filter(Process.father == process_id).first()
            if process:
                db.delete(process)
                db.commit()
        except Exception as e:
            db.rollback()  # Revertir la transacción en caso de error
            raise e
