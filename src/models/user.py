from dataclasses import dataclass
import uuid

@dataclass
class RawUser:
    id: int # same as telegram id

@dataclass
class User(RawUser):
    is_tutor: bool

@dataclass
class RawStudent(RawUser):
    name: str
    group_id: uuid.UUID

@dataclass
class Student(RawStudent, User):
    is_tutor = False
