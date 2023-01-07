import os
import pathlib
import shutil
from pymongo import MongoClient, database

from config import GROUP_COLLECTION_NAME, RUNTIME_FOLDER, \
        TEST_COLLECTION_NAME, TESTS_FOLDERNAME, USER_COLLECTION_NAME, \
        WRITTEN_TEST_COLLECTION_NAME, WRITTEN_TESTS_FOLDERNAME

from .tests import TestsTable
from .users import UsersTable
from .groups import GroupsTable


class DataBase():

    def __init__(self,
            db_url: str) -> None:
        self.__db_client = MongoClient(db_url)
        db = self.create_database()

        self.groups = GroupsTable(db)
        self.tests = TestsTable(db)
        self.users = UsersTable(db)

        self.create_runtime_folders()


    #region Runtime file storage

    def create_runtime_folders(self) -> None:
        pathlib.Path(f'{RUNTIME_FOLDER}/{TESTS_FOLDERNAME}').mkdir(\
                parents=True, exist_ok=True)
        pathlib.Path(f'{RUNTIME_FOLDER}/{WRITTEN_TESTS_FOLDERNAME}').mkdir(\
                parents=True, exist_ok=True)

    def clear_tests_folder(self) -> None:
        path = f'{RUNTIME_FOLDER}/{TESTS_FOLDERNAME}'
        self.__clear_folder(path)

    def clear_written_tests_folder(self) -> None:
        path = f'{RUNTIME_FOLDER}/{WRITTEN_TESTS_FOLDERNAME}'
        self.__clear_folder(path)

    def clear_runtime_folders(self) -> None:
        self.__clear_folder(RUNTIME_FOLDER)

    def __clear_folder(self, path: str) -> None:
        shutil.rmtree(path)
        pathlib.Path(path).mkdir(parents=True)

    #endregion


    #region Database

    def create_database(self) -> database.Database:
        db = self.__db_client.get_database(os.environ['MONGODB_DATABASE'])
        self.__create_db_collection(db, GROUP_COLLECTION_NAME)
        self.__create_db_collection(db, TEST_COLLECTION_NAME)
        self.__create_db_collection(db, WRITTEN_TEST_COLLECTION_NAME)
        self.__create_db_collection(db, USER_COLLECTION_NAME)
        return db

    def __create_db_collection(self, db: database.Database, name: str) -> None:
        collection = db.get_collection(name)
        insertion = collection.insert_one({})
        collection.delete_one({ '_id': insertion.inserted_id })

    def clear_database(self) -> None:
        self.__db_client.drop_database(os.environ['MONGODB_DATABASE'])
        self.create_database()

    #endregion
