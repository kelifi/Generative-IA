import mimetypes
import tempfile
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.responses import FileResponse

from source.schemas.api_schemas import FileInputSchema
from source.services import sources_service
from tests.conftest import test_source_service


@pytest.mark.asyncio
async def test_preview_document(test_source_service, monkeypatch):
    """Test if the file with a certain file_id corresponds to a non pdf file it is returned without highlight"""
    user_id = str(uuid4())
    file_id = str(uuid4())
    file_input = FileInputSchema(content="highlight me please but only if i am a pdf file")

    docx_mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    file_name = 'test_document.docx'

    file_type_response = [{'raw': {'path': f'test/{file_name}', 'size': 86876,
                                   'creation time': 'Sun, 08 Oct 2023 19:49:53 +0000',
                                   'Content type': f'application/{docx_mime_type}',
                                   'file name': 'test_document.docx',
                                   'original_file_name': file_name}, '_folder': 'some_folder'}]

    with tempfile.SpooledTemporaryFile() as file:
        mime_type, _ = mimetypes.guess_type("test_document.docx")
        ingested_file_from_fh = FileResponse(file.name, media_type=mime_type,
                                             headers={"Content-Disposition": f"attachment; filename={file_name}"})

    return_values = [file_type_response, ingested_file_from_fh]

    async def mock_multiple_make_request(*args, **kwargs):
        return return_values.pop(0)

    monkeypatch.setattr(sources_service, 'make_request', mock_multiple_make_request)

    result = await test_source_service.preview_document(user_id=user_id, file_id=file_id, file_input=file_input)

    assert isinstance(result, FileResponse)
    assert result.status_code == HTTPStatus.OK
    assert result.media_type == docx_mime_type
    assert result.raw_headers == [(b'content-disposition', b'attachment; filename=test_document.docx'), (
    b'content-type', b'application/vnd.openxmlformats-officedocument.wordprocessingml.document')]
