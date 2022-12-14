from pymongo import MongoClient

from .tests import TestsTable
from .users import UsersTable
from .groups import GroupsTable


DATABASE_NAME = 'flying-bot'

class DataBase():

    def __init__(self,
            db_url: str) -> None:
        self.__db_client = MongoClient(db_url)
        db = self.__db_client[DATABASE_NAME]

        self.groups = GroupsTable(db)
        self.tests = TestsTable(db)
        self.users = UsersTable(db)
