import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import Field

from configuration.config import ReportGenerationConfig
from configuration.injection_container import DependencyContainer
from source.schemas.common_schema import ReportDataModel
from source.services.reports_service import ReportService
from source.utils.common_utils import delete_file

report_router = APIRouter(prefix="/report")


@report_router.post("")
@inject
def generate_esg_report(
        background_tasks: BackgroundTasks,
        report: ReportDataModel,
        user_id: str,
        report_id: str,
        report_service: ReportService = Depends(Provide[DependencyContainer.report_service]),
        report_generation_config: ReportGenerationConfig = Depends(
            Provide[DependencyContainer.report_generation_config])
):
    """
    Generate a PDF report, save it, and return the file as a response.

    """

    report_service.generate_pdf_report(dict(report).get("data"), report_generation_config.tmp_file_path)
    report_service.save_report_service(report, user_id, report_id)

    file_response = FileResponse(
        path=os.path.join(os.getcwd(), report_generation_config.tmp_file_path),
        media_type="application/pdf",
        filename="Report.pdf"
    )
    background_tasks.add_task(delete_file, report_generation_config.tmp_file_path)
    return file_response
