import uuid
from typing import List

from ..models.test import RawTest, Test


class TestsTable():

    def __init__(self) -> None:
        self.entities: List[Test] = []

    def create_test(self, source: RawTest) -> Test:
        test = Test(source.name, uuid.uuid4())
        self.entities.append(test)
        return test

    def get_tests(self) -> List[Test]:
        return self.entities
