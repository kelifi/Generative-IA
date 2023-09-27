from contextlib import contextmanager
from typing import Generator

from configuration.logging_setup import logger
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker

from source.exceptions.service_exceptions import OopsNoDBError
from source.models.common_models import Base
from source.models.model_table import Model_base


class DBHelper:
    def __init__(self, db_url):
        self.database_url = db_url

        # Create engine to connect to database
        try:
            self.engine = create_engine(
                self.database_url,
                pool_recycle=600,
                pool_pre_ping=True,
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
            logger.info("creating Database")
            self.engine.connect()
            Base.metadata.create_all(self.engine, Base.metadata.tables.values(), checkfirst=True)
            Model_base.metadata.create_all(self.engine, Model_base.metadata.tables.values(), checkfirst=True)
            logger.info("Database initialized successfully!")
        except SQLAlchemyError as database_initialisation_error:
            logger.error(f"Failed to initialize Database: {database_initialisation_error}")
