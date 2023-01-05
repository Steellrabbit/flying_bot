from pymongo import database

from typing import Any, cast

from config import GROUP_COLLECTION_NAME

from ..models.group import RawGroup, Group


class GroupsTable():

    def __init__(self,
            db: database.Database) -> None:
        self.__collection = db[GROUP_COLLECTION_NAME]

    def create(self, source: RawGroup) -> Group:
        doc = { 'name': source.name }
        insert_result = self.__collection.insert_one(doc)
        found = self.__collection.find_one({ '_id': insert_result.inserted_id })
        return self.__from_document(cast(dict, found))

    def get_all(self) -> list[Group]:
        found = self.__collection.find()
        return list(map(lambda doc: self.__from_document(doc), found))

    def get(self, property: str, value: Any) -> Group | None:
        found = self.__collection.find_one({ property: value })
        if found is None: return
        return self.__from_document(found)

    def remove_all(self) -> None:
        self.__collection.delete_many({})

    def __from_document(self, doc: dict) -> Group:
        return Group(doc['name'], doc['_id'])
    
