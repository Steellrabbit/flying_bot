from .tests import TestsTable
from .users import UsersTable
from .groups import GroupsTable


class DataBase():

    def __init__(self) -> None:
        self.groups = GroupsTable()
        self.tests = TestsTable()
        self.users = UsersTable()
