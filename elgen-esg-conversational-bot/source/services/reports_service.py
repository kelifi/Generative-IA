from fastapi.encoders import jsonable_encoder
from loguru import logger

from source.helpers.report_crud import MongoDatabaseCrud
from source.schemas.common_schema import ReportModel
from source.utils.pdf_utils import dict_to_pdf


class ReportService:
    def __init__(self, db_crud: MongoDatabaseCrud):
        self.db_crud = db_crud

    def save_report_service(self, report: ReportModel, user_id: str, report_id: str) -> ReportModel:
        report_data = jsonable_encoder(ReportModel(**dict(report), user_id=user_id, report_id=report_id))
        check_existing_report = self.db_crud.report_list_helper(self.db_crud.find_report_by_user_id(user_id, report_id))
        if not check_existing_report:
            logger.info(f"Add new report for user {user_id}")
            return ReportModel(**self.db_crud.save_report(report_data))
        logger.info(f"Report {report_id} already exists for user {user_id}")
        return ReportModel(**self.db_crud.update_report_by_id(report_data))

    @staticmethod
    def generate_pdf_report(report_data_dict, file_path):
        logger.info("Generating PDF report")
        dict_to_pdf(report_data_dict, file_path)
