from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from my_celery.config.settings import settings

psql_engine = create_engine(
    settings.POSTGRES_DATABASE_URL_CELERY,
    echo=False,
    pool_pre_ping=True,    
    pool_size=20,          
    max_overflow=40,       
    pool_timeout=10,      
    pool_recycle=3600,     
    pool_use_lifo=True     
)
SessionLocal = sessionmaker(bind=psql_engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()