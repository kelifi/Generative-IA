import tempfile
from asyncio import TimeoutError, CancelledError
from functools import partial
from io import BytesIO
from typing import Dict, Any, Union

import async_timeout
from aiohttp import ClientResponse, FormData, ClientSession, ClientConnectorError, ContentTypeError
from circuitbreaker import circuit
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from inflection import camelize
from pydantic import BaseModel

from configuration.config import logger
from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import MetadataObjParseError
from source.models.enums import RequestMethod


class CamelModel(BaseModel):
    """
    class configured to return fields in camelCase for all the child classes
    """

    def get_by_alias(self, alias):
        for field, details in self.__fields__.items():
            if details.alias == alias:
                return self.__getattribute__(field)
        raise AttributeError(f"'{self.__class__}' object has no attribute with alias '{alias}'")

    class Config:
        """
        Config to return fields as camelCase but keep using snake_case in dev
        """

        alias_generator = partial(camelize, uppercase_first_letter=False)
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        use_enum_values = True


async def file_to_data(payload_obj, data: FormData, files_field_name) -> FormData:
    """
    Args:
        payload_obj: convert file to aio http form data so it can be send in the request
    Returns: aiohttp FormData that could be used on async methods
    """
    temp = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
    temp.name = payload_obj.filename
    try:
        temp.writelines(payload_obj.file)
        temp.seek(0)
        data.add_field(files_field_name, temp.read(), filename=payload_obj.filename)
        temp.close()
    except Exception as exception:
        logger.exception(exception)
    return data


@circuit(failure_threshold=10, recovery_timeout=10)
async def handle_file_upload(
        file: UploadFile,
        service_url: str,
        uri: str,
        method: RequestMethod,
        file_data_params: dict = None,
        query_params: dict = None,
        headers: Dict = None,
        cookies: Any = None,
        file_field_name: str = "file"
):
    data = FormData()
    if file_data_params:
        for key, value in file_data_params.items():
            data.add_field(key, value)
    data = await file_to_data(file, data, file_field_name)
    if query_params is None:
        query_params = {}
    uri = uri.lstrip('/')
    if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        raise HTTPException(status_code=405, detail=f"Method {method} is not allowed")

    with async_timeout.timeout(delay=None):
        try:
            async with ClientSession() as session:
                request = getattr(session, method)
                async with request(
                        url=f"{service_url.rstrip('/') + '/' + uri.lstrip('/')}",
                        headers=headers,
                        data=data,
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
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Service is unavailable.'
            )
        except ContentTypeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Service error.'
            )


def make_query_params(**kwargs) -> Dict[str, str]:
    """
    Used to make query_params dict compatible with make_request. Library aiohttps does not accept
    None values for query params but can accept empty dict for query_params. So you should only add
    query_params when they have values.

    :**kwargs : put your query params here
    :dict : resulting query params dict

    """
    return {key: f'{value}' for key, value in kwargs.items() if value is not None}


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


async def handle_data_by_response_content_type(response) -> Union[StreamingResponse, FileResponse]:
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


def parse_metadata_id_object(metadata_object: list[dict]) -> (str, str):
    """Parse the metadata object from  /medata_id in File handler, the metadata object is a list containing 1 element"""
    try:
        extracted_file_type = metadata_object[0].get("raw").get("Content type").split('/')[1]
        file_name = metadata_object[0].get("raw").get("file name")
    except IndexError:
        raise MetadataObjParseError(detail=f"Could not parse the following metadata object: {metadata_object}")

    if not extracted_file_type or not file_name:
        raise MetadataObjParseError(detail=f"Could not fetch the extracted_file_type or file_name: {metadata_object}")
    return extracted_file_type, file_name
