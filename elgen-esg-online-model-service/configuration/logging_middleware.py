import logging
import pathlib
import time
from typing import Callable, Union, Any, Optional, Dict, Tuple
from uuid import uuid4

from fastapi import FastAPI, Request, status
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from configuration.logging_conf import otlp_config

otlp_exporter = OTLPSpanExporter(endpoint=otlp_config.OTLP_ENDPOINT)

provider = TracerProvider()
processor = BatchSpanProcessor(span_exporter=otlp_exporter)
provider.add_span_processor(span_processor=processor)
trace.set_tracer_provider(tracer_provider=provider)
tracer = trace.get_tracer(__name__)

status_code_500 = status.HTTP_500_INTERNAL_SERVER_ERROR
app_name = pathlib.Path(__file__).parent.parent.name


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app: FastAPI,
            *,
            logger: logging.Logger
    ) -> None:
        self._logger = logger
        super().__init__(app)

    async def dispatch(self,
                       request: Request,
                       call_next: Callable
                       ) -> Response:
        request_id: str = request.headers.get('x-correlation-id') or str(uuid4())

        with tracer.start_as_current_span("server_request") as span:
            response, response_dict = await self._log_response(call_next,
                                                               request,
                                                               request_id
                                                               )
            request_logging__dict = await self._log_request(request)
            logging_dict = {"correlation_id": request_id, "log_type": "request",
                            "app_name": app_name,
                            "request": request_logging__dict,
                            "response": response_dict,
                            "otelSpanID": span.get_span_context().span_id,
                            # added them manually because there weren't being injected properly
                            "otelTraceID": span.get_span_context().trace_id}

            # A response can be None if an unhandled exception occurred
            if response:
                self._logger.info(logging_dict)
                return response

            return Response(status_code=status_code_500)

    async def _log_request(
            self,
            request: Request
    ) -> Dict[str, Union[str, Any]]:
        """Logs request part
            Arguments:
           - request: Request

        """

        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"
        operation_name = request.scope.get('route').name if request.scope.get('route') else None
        return {"http.method": request.method,
                "http.path": path,
                'operation_name': operation_name,
                "log_type": "request",
                "session_id": request.cookies.get('sessionId')
                }

    async def _log_response(self,
                            call_next: Callable,
                            request: Request,
                            request_id: str
                            ) -> Tuple[Optional[Response], Dict[str, Union[str, int]]]:
        """Logs response part

               Arguments:
               - call_next: Callable (To execute the actual path function and get response back)
               - request: Request
               - request_id: str (uuid)
               Returns:
               - response: Response
               - response_logging: str
        """

        start_time = time.perf_counter()
        response = await self._execute_request(call_next, request, request_id)
        finish_time = time.perf_counter()
        execution_time = finish_time - start_time

        if response:
            overall_status = "successful" if response.status_code < 400 else "failed"

            response_logging_dict = {
                "status": overall_status,
                "http.status_code": response.status_code,
                "duration_ms": f"{execution_time:0.4f}s"
            }

            return response, response_logging_dict

        # In case of an unhandled error, the response object would be None
        response_logging = {
            "status": "Unhandled error",
            "http.status_code": status_code_500,
            "duration_ms": f"{execution_time:0.4f}s"
        }

        return None, response_logging

    async def _execute_request(self,
                               call_next: Callable,
                               request: Request,
                               request_id: str
                               ) -> Response:
        """Executes the actual path function using call_next.
               It also injects "X-API-Request-ID" header to the response.

               Arguments:
               - call_next: Callable (To execute the actual path function
                            and get response back)
               - request: Request
               - request_id: str (uuid)
               Returns:
               - response: Response
        """
        try:
            response: Response = await call_next(request)
            # Kickback X-Request-ID
            response.headers["x-correlation-id"] = request_id
            return response

        except Exception as general_error:
            self._logger.exception(
                {
                    "path": f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path,
                    "method": request.method,
                    "reason": general_error,
                    "session_id": request.cookies.get('sessionId'),
                    "status": status_code_500,
                    "overall_status": "failed",
                    "correlation_id": request_id
                }
            )