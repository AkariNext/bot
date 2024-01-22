from contextlib import contextmanager
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///database.db', echo=True)

LocalSession = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    session = LocalSession()
    try:
        yield session
        session.commit()
        
    except:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def scoped_session():
    return get_db()
