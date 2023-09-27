from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

health_check_router = APIRouter()


@health_check_router.get(path="/healthz", summary="Check if the service is up and running or not")
def determine_service_health() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})
