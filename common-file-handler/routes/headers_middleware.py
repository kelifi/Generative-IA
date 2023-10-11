import json

from starlette.middleware.base import BaseHTTPMiddleware

from authorization.db.crud import get_additional_info_by_id


class HeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if '/get_file' == request.url.path and response.status_code == 200:
            file_id = request.query_params.get("file_id")
            if file_id:
                response.headers["additional-info"] = json.dumps(get_additional_info_by_id(file_id)["additional_info"])
        return response
