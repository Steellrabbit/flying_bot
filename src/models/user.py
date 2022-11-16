from dataclasses import dataclass

@dataclass
class RawUser:
    id: int # same as telegram id

@dataclass
class User(RawUser):
    is_tutor: bool

@dataclass
class RawStudent(RawUser):
    name: str
    group_id: int

@dataclass
class Student(RawStudent, User):
    is_tutor = False
