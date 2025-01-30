import psycopg

from app import settings


class PostgresDatabase:
    def __init__(self):
        self.connection_string = ('postgresql://'
            + settings.Postgres.USER_NAME + ':'
            + settings.Postgres.PASSWORD + '@'
            + settings.Postgres.HOST_URL + '/'
            + settings.Postgres.DATABASE_NAME)
    
    def open_connection(self):
        self.connection = psycopg.connect(self.connection_string)
    
    def close_connection(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query):
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            self.connection.commit()
