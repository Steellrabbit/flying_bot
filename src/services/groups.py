from typing import List
import uuid

from ..models.group import RawGroup, Group


class GroupsTable():

    def __init__(self) -> None:
        self.entities: List[Group] = []

    def create_group(self, source: RawGroup) -> Group:
        group = Group(source.name, uuid.uuid4())
        self.entities.append(group)
        return group

    def get_groups(self) -> List[Group]:
        return self.entities
