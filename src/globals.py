from src.storage import Storage, CloudinaryStorage
from src.database import Database


storage: Storage = None
database: Database = None


def globals_init() -> None:
    global storage, database    
    storage = CloudinaryStorage()
    database = Database()
    database.open()
    storage.open()


def globals_close() -> None:
    global storage, database
    database.close()
    storage.close()


def globals_get_storage() -> Storage:
    global storage
    return storage


def globals_get_database() -> Database:
    global database
    return database
    