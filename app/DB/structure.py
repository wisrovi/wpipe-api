import os

from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    JSON,
    ForeignKey,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.mysql import JSON as MySQLJSON  # Importar JSON para MySQL


Base = declarative_base()


is_sqlite = False
is_mysql = True


MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
SERVER = os.environ.get("SERVER")


if is_sqlite:
    # Configuración de la base de datos
    DATABASE_URL = "sqlite:///example.db"  # ./example.db
    # DATABASE_URL = "sqlite:////backup_db/example.db"  # /backup_db/example.db

    # Clase para la tabla Workers
    class Worker(Base):
        __tablename__ = "workers"

        id = Column(String, primary_key=True, index=True)  # UUID
        nombre = Column(String)
        version = Column(String)
        last_healthcheker = Column(DateTime)
        datetime = Column(DateTime)
        tasks = Column(JSON)  # Lista de tareas almacenadas como JSON

    # Clase para la tabla Processes
    class Process(Base):
        __tablename__ = "processes"

        father = Column(String, primary_key=True)
        process = Column(String, ForeignKey("workers.id"))
        created = Column(DateTime)
        finished = Column(DateTime, nullable=True)  # Nullable por si no se ha terminado
        status = Column(String)
        error = Column(String)

        worker = relationship("Worker")

    # Clase para la tabla HistoryTask
    class HistoryTask(Base):
        __tablename__ = "history_tasks"

        uuid = Column(String, primary_key=True)
        name = Column(String)
        status = Column(String)
        order = Column(Integer)
        version = Column(String)
        create = Column(DateTime)
        started = Column(DateTime)
        update = Column(DateTime)
        details = Column(String, nullable=True)
        father = Column(String, ForeignKey("processes.father"))

        process_relation = relationship("Process")

elif is_mysql:
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{SERVER}/{MYSQL_DATABASE}"
    )

    # Clase para la tabla Workers
    class Worker(Base):
        __tablename__ = "workers"

        id = Column(
            String(100), primary_key=True, index=True
        )  # UUID con longitud especificada
        nombre = Column(String(255))  # Especifica la longitud
        version = Column(String(50))  # Especifica la longitud
        last_healthcheker = Column(DateTime)
        datetime = Column(DateTime)
        tasks = Column(MySQLJSON)  # Cambia a MySQL JSON si es necesario

    # Clase para la tabla Processes
    class Process(Base):
        __tablename__ = "processes"

        father = Column(String(100), primary_key=True)  # Especifica la longitud
        process = Column(
            String(100), ForeignKey("workers.id")
        )  # Especifica la longitud
        created = Column(DateTime)
        finished = Column(DateTime, nullable=True)  # Nullable por si no se ha terminado
        status = Column(String(50))  # Especifica la longitud
        error = Column(
            String(4096), nullable=True
        )  # Especifica la longitud y permite nulos

        worker = relationship("Worker")

    # Clase para la tabla HistoryTask
    class HistoryTask(Base):
        __tablename__ = "history_tasks"

        uuid = Column(String(100), primary_key=True)  # Especifica la longitud
        name = Column(String(255))  # Especifica la longitud
        status = Column(String(50))  # Especifica la longitud
        order = Column(Integer)
        version = Column(String(50))  # Especifica la longitud
        create = Column(DateTime)
        started = Column(DateTime)
        update = Column(DateTime)
        details = Column(
            String(4096), nullable=True
        )  # Especifica la longitud y permite nulos
        father = Column(
            String(100), ForeignKey("processes.father")
        )  # Especifica la longitud

        process_relation = relationship("Process")


engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)


# Función para obtener la sesión de la base de datos
def get_session():
    return SessionLocal()


# datetime


def generate_datetime():
    """Genera la fecha actual como un objeto datetime."""
    return datetime.now()


def generate_datetime_string():
    """Genera una fecha actual en formato string: año/mes/día-hora:minuto:segundo:milisegundos."""
    now = datetime.now()
    formatted_date = now.strftime("%Y/%m/%d-%H:%M:%S.%f")[
        :-3
    ]  # Formato con milisegundos
    return formatted_date


def string_to_datetime(date_string):
    """Convierte un string en formato año/mes/día-hora:minuto:segundo:milisegundos a un objeto datetime."""
    return datetime.strptime(date_string, "%Y/%m/%d-%H:%M:%S.%f")


def compare_dates_in_seconds(date_string1, date_string2):
    """Compara dos fechas en formato string y devuelve la diferencia en segundos."""
    date1 = string_to_datetime(date_string1)
    date2 = string_to_datetime(date_string2)
    difference = abs(
        (date2 - date1).total_seconds()
    )  # Se usa abs para obtener un valor positivo
    return difference
