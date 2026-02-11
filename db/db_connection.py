from contextlib import contextmanager
import mysql.connector

@contextmanager
def get_database_connection():
    """ Context manager for handling database connection. """
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="py_diski_webshops"
    )
    try:
        yield connection  # Yield the connection to be used in the with block
    finally:
        if connection.is_connected():
            connection.close()  # Ensure connection is closed after use
