from pymongo import database

from typing import Any
import uuid

from ..models.group import RawGroup, Group
from ..utils.get_from_list import get_from_list


GROUP_COLLECTION = 'groups'

class GroupsTable():

    def __init__(self,
            db: database.Database) -> None:
        self.__collection = db[GROUP_COLLECTION]

    def create(self, source: RawGroup) -> Group:
        doc = { 'name': source.name }
        insert_result = self.__collection.insert_one(doc)
        found = self.__collection.find_one({ '_id': insert_result.inserted_id })
        return self.__from_document(found)

    def get_all(self) -> list[Group]:
        found = self.__collection.find()
        return list(map(lambda doc: self.__from_document(doc), found))

    def get(self, property: str, value: Any) -> Group | None:
        found = self.__collection.find_one({ property: value })
        if found is None: return
        return self.__from_document(found)

    def __from_document(self, doc: dict) -> Group:
        return Group(doc['name'], doc['_id'])
