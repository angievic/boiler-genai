from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = "postgresql://admin:123asd456@db/testdb"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully")
    except SQLAlchemyError as e:
        print(f"An error occurred while creating database tables: {e}")
        raise

def get_session():
    with Session(engine) as session:
        yield session
