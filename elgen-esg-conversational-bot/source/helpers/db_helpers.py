from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker

from source.exceptions.service_exceptions import OopsNoDBError
from source.models.db_models import Base, User
from source.utils.constants import default_user_id


class DBHelper:
    def __init__(self, db_url):
        self.database_url = db_url

        # Create engine to connect to database
        try:
            self.engine = create_engine(
                self.database_url,
                connect_args={
                    'options': '-csearch_path=public',
                    'application_name': 'elgen-esg-conversational-bot-service',
                },
                pool_recycle=600,
                pool_pre_ping=True
            )
        except Exception as engine_error:
            logger.error(engine_error)

    def create_db_local_session(self) -> scoped_session | None:
        """
        Create the engine ORM to interact with a Database
        :return: local session if one was created, None otherwise
        """
        return scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False,
            )
        )

    @contextmanager
    def session(self) -> Generator[scoped_session, None, None]:
        """
        Context manager that provides transaction management for nested blocks.
        A transaction is started when the block is entered and then either
        committed if the block exists without incident, or rolled back if an error is raised
        :return: Scoped Session
        """
        session = self.create_db_local_session()
        if session is None:
            raise OopsNoDBError("Session not created: Connection to Database could not be established!")
        try:
            yield session
            session.commit()
        except Exception as error:
            session.rollback()
            raise error
        finally:
            session.close()

    def init_database(self):
        """
        Initializes a database with the necessary tables
        :return: True if the database is initialized successfully, False otherwise
        """
        try:
            self.engine.connect()
            Base.metadata.create_all(self.engine, Base.metadata.tables.values(), checkfirst=True)
            logger.info("Creating default user...")
            self.create_default_user()
            logger.success("Database initialized successfully!")
        except SQLAlchemyError as database_initialisation_error:
            logger.error(f"Failed to initialize Database: {database_initialisation_error}")

    def create_default_user(self):
        """Checks if the default user exists in the database. If not, it creates it"""
        with self.session() as session:
            user = session.query(User).filter_by(id=default_user_id).first()
            if not user:
                default_user = User()
                default_user.id = default_user_id
                default_user.creation_date = datetime.now()
                session.add(default_user)
                session.commit()
