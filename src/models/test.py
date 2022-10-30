import uuid
from dataclasses import dataclass


@dataclass
class RawTest:
    name: str

@dataclass
class Test(RawTest):
    id: uuid.UUID
