from psycopg2 import pool
from psycopg2.extras import RealDictCursor


class Database:
    __connection_pool = None

    @staticmethod
    def initialise(**kwargs):
        """
        initialise database
        :param kwargs: keyworded variable that contains database inforamtion
        :return: database
        """
        Database.__connection_pool = pool.SimpleConnectionPool(1, 10, **kwargs)

    @staticmethod
    def get_connection():
        """
        Get a free connection and assign it to 'key' if not None.
        :return: connection key
        """
        return Database.__connection_pool.getconn()

    @staticmethod
    def return_connection(connection):
        """
        Put away a connection.
        :param connection: connection
        :return: closed connection
        """
        Database.__connection_pool.putconn(connection)

    @staticmethod
    def close_all_connections():
        """
        close connections
        :return:
        """
        Database.__connection_pool.closeall()


class CursorFromConnectionPool:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:
            self.conn.rollback()
        else:
            self.cursor.close()
            self.conn.commit()
        Database.return_connection(self.conn)


class RealDictCursorFromConnectionPool:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.cursor

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_value:
            self.conn.rollback()
        else:
            self.cursor.close()
            self.conn.commit()
        Database.return_connection(self.conn)
