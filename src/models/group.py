import uuid
from dataclasses import dataclass


@dataclass
class RawGroup:
    name: str


@dataclass
class Group(RawGroup):
    id: uuid.UUID
