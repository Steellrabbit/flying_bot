from typing import List, Union

from ..models.user import User, Student, RawStudent


class UsersTable():

    def __init__(self) -> None:
        self.users: List[User] = []


    # region Tutor

    def has_tutor(self) -> bool:
        return len([user for user in self.users if user.is_tutor]) != 0

    def create_tutor(self, id: int) -> User:
        tutor = User(id, True)
        self.users.append(tutor)
        return tutor

    # endregion


    # region Student

    def create_student(self, source: RawStudent) -> Student:
        student = Student(source.id, False, source.name, source.group_id)
        self.users.append(student)
        return student

    # endregion


    # region User

    def get_user(self, id: int) -> Union[User, None]:
        search_result = [user for user in self.users if user.id == id]
        if len(search_result) == 0:
            return None
        return search_result[0]

    # endregion
