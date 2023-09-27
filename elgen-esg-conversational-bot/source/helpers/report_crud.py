import time
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from loguru import logger
from pymongo import MongoClient, cursor
from pymongo.cursor import Cursor

from configuration.config import MongoBaseConfig
from source.schemas.common_schema import ReportModel


class MongoConnectionProvider:
    def __init__(self, mongo_config: MongoBaseConfig):
        self.client = MongoClient(host=mongo_config.HOST, port=mongo_config.PORT, username=mongo_config.USER,
                                  password=mongo_config.PASSWORD)
        self.data_base = self.client.get_database(mongo_config.DATABASE)
        self.collection = self.data_base.get_collection(mongo_config.ID_COLLECTION)


class MongoDatabaseCrud:
    """
    this class is used to initiate the mongo db and create the crud services
    """

    def __init__(self, mongo_connection_provider: MongoConnectionProvider):
        self.mongo_connection_provider = mongo_connection_provider

    def save_report(self, report: dict) -> dict:
        """
        This function will save a report with specific type
        """
        inserted_report = self.mongo_connection_provider.collection.insert_one(report)
        logger.info("Report inserted with id {} in the database".format(inserted_report.inserted_id))
        return self.mongo_connection_provider.collection.find_one({"_id": inserted_report.inserted_id})

    def find_report_by_user_id(self, user_id: str, report_id: str) -> Cursor:
        """
        This function will search for report by user id and report id
        """
        return self.mongo_connection_provider.collection.find({"user_id": user_id, "report_id": report_id})

    def update_report_by_id(self, new_report_data) -> dict:
        """
        This function will update the data of report by user_id and report_id
        """
        updated_report = self.mongo_connection_provider.collection.update_one(
            {"user_id": new_report_data["user_id"], "report_id": new_report_data["report_id"]},
            {"$set": {"data": new_report_data["data"],
                      "modified_time":
                          datetime.fromtimestamp(time.time(), None)}})
        logger.info(f"data of report was successfully updated : {updated_report.raw_result}")
        return self.mongo_connection_provider.collection.find_one(
            {"user_id": new_report_data["user_id"], "report_id": new_report_data["report_id"]})

    @staticmethod
    def report_list_helper(document_cursor: cursor.Cursor):
        try:
            return [jsonable_encoder(ReportModel(**document)) for document in document_cursor]
        except Exception as validation_error:
            logger.error("Error Parsing document json : {}".format(validation_error))
