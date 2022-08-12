import os

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("provide db file")

    if not os.path.exists(db_file.strip()):
        with open(db_file.strip(), 'w'):
            pass

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"DB CONNECTION: {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    # noinspection PyUnresolvedReferences
    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    if not callable(__factory):
        raise Exception("db not initialized")
    return __factory()


if __name__ == '__main__':
    global_init('../db/db.sqlite3')