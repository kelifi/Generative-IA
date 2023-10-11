import tempfile
from asyncio import TimeoutError, CancelledError
from io import BytesIO
from typing import Dict, Any

import async_timeout
import sqlparse
from aiohttp import ClientResponse, ClientSession, ClientConnectorError, ContentTypeError
from circuitbreaker import circuit
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from langdetect import detect, LangDetectException

from configuration.logging_setup import logger
from source.exceptions.api_exception_handler import NotOkServiceResponse
from source.schemas.chat_schema import QuestionLanguageEnum
from source.schemas.common import RequestMethod


@circuit(failure_threshold=10, recovery_timeout=10)
async def make_request(service_url: str,
                       uri: str,
                       method: RequestMethod,
                       query_params: Dict = None,
                       body: Any = None,
                       headers: dict = None,
                       cookies: Any = None,
                       keycloak_request_option: bool = False
                       ):
    """

    :param service_url: the url of the service to call
    :param uri: the endpoint to call
    :param method: the method to use
    :param query_params: a dict of query params, if any
    :param body: a dict to pass in the body of the request, if any
    :param headers: the request headers
    :param cookies: the request cookies
    :param keycloak_request_option: optional value to pass the body as 'data' in the request
    :return: a json response
    :raises: a HTTP exception
    """
    if headers is None:
        headers = {}
    if query_params is None:
        query_params = {}
    uri = uri.lstrip('/')
    headers.pop("content-length", None)  # causes an infinite loop if sent to service
    with async_timeout.timeout(180):
        try:
            service_name = service_url.replace("http://", "").split(".")[0]
            async with ClientSession() as session:
                request = getattr(session, method)
                async with request(
                        url=f"{service_url.rstrip('/') + '/' + uri.strip('/')}",
                        headers=headers,
                        json=(None if keycloak_request_option else body),
                        data=(body if keycloak_request_option else None),
                        params=query_params,
                        cookies=cookies
                ) as response:
                    if response.ok:
                        return await handle_data_by_response_content_type(response)
                    else:
                        try:
                            json_response = await response.json()
                            return NotOkServiceResponse(status_code=response.status, content=json_response)
                        except Exception:
                            detail = await response.text()
                            raise HTTPException(status_code=response.status, detail=detail)
        except ClientConnectorError:
            logger.exception(f'Service {service_name} is unavailable.')
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Service is unavailable.'
            )
        except ContentTypeError:
            logger.exception(f'Service error: {service_name}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Service error.'
            )
        except (CancelledError, TimeoutError) as timeout_exception:
            logger.exception(
                "This request has timed out and has been cancelled, "
                f"the target service {service_name} took too long to respond or is unavailable"
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail='This request has timed out and has been cancelled, please retry.'
            )


async def handle_data_by_response_content_type(response):
    """
    handler request response by response content type
    Args:
        response: the http request response

    Returns: the data after handling it

    """
    request_response: ClientResponse = response
    if request_response.content_type == 'application/json':
        data = await response.json()
        return data
    if request_response.content_type == 'application/x-zip-compressed':
        zipped_file = BytesIO()
        data = await response.read()
        zipped_file.write(data)
        zipped_file.seek(0)
        response_stream = StreamingResponse(zipped_file, media_type="application/x-zip-compressed")
        response_stream.headers["Content-Disposition"] = "attachment; filename=zipped.zip"
        return response_stream
    else:
        data = await response.read()
        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as file:
            file.write(data)
        data = FileResponse(file.name, media_type=response.content_type)
        data.headers['Content-Security-Policy'] = r'default-src \'self\''
        return data


def detect_language(text: str) -> QuestionLanguageEnum:
    """
    Detect language from text
    :param text: text
    :return: language of text
    """
    if text:
        if len(text.split(" ")) < 2:
            return QuestionLanguageEnum.EN
        try:
            language = detect(text)
        except LangDetectException:
            return QuestionLanguageEnum.EN
        return language.lower()


def is_select_query(sql_query):
    # Use sqlparse to parse the SQL query
    parsed_query = sqlparse.parse(sql_query)
    first_token = next(token for token in parsed_query[0].tokens if not token.is_whitespace)
    return first_token.normalized.upper() == 'SELECT' and len(parsed_query) == 1
