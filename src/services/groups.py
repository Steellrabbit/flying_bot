from typing import Any
import uuid

from ..models.group import RawGroup, Group
from ..utils.get_from_list import get_from_list


class GroupsTable():

    def __init__(self) -> None:
        self.entities: list[Group] = []

    def create(self, source: RawGroup) -> Group:
        group = Group(source.name, uuid.uuid4())
        self.entities.append(group)
        return group

    def get_many(self) -> list[Group]:
        return self.entities

    def get(self, property: str, value: Any) -> Group | None:
        return get_from_list(self.entities, property, value)
