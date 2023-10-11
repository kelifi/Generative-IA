import logging
import mimetypes
import os
import random
import re
import string
import unicodedata
from typing import Type
from urllib import parse

import dateutil.parser
import pytz
from stevedore import driver

from authorization.models.structures import FileInDB
from core import exceptions

logger = logging.getLogger(__name__)


def make_provider(name: str, auth: dict, credentials: dict, settings: dict, **kwargs):
    r"""Returns an instance of :class:`waterbutler.core.provider.BaseProvider`

    :param str name: The name of the provider to instantiate. (s3, box, etc)
    :param dict auth:
    :param dict credentials:
    :param dict settings:
    :param dict \*\*kwargs: currently there to absorb ``callback_url``

    :rtype: :class:`waterbutler.core.provider.BaseProvider`
    """
    try:
        manager = driver.DriverManager(
            namespace='waterbutler.providers',
            name=name,
            invoke_on_load=True,
            invoke_args=(auth, credentials, settings),
            invoke_kwds=kwargs,
        )
    except RuntimeError:
        raise exceptions.ProviderNotFound(name)

    return manager.driver


def normalize_datetime(date_string):
    if date_string is None:
        return None
    parsed_datetime = dateutil.parser.parse(date_string)
    if not parsed_datetime.tzinfo:
        parsed_datetime = parsed_datetime.replace(tzinfo=pytz.UTC)
    parsed_datetime = parsed_datetime.astimezone(tz=pytz.UTC)
    parsed_datetime = parsed_datetime.replace(microsecond=0)
    return parsed_datetime.isoformat()


def strip_for_disposition(filename):
    """Convert given filename to a form useable by a non-extended parameter.

    The permitted characters allowed in a non-extended parameter are defined in RFC-2616, Section
    2.2.  This is a subset of the ascii character set. This function converts non-ascii characters
    to their nearest ascii equivalent or strips them if there is no equivalent.  It then replaces
    control characters with underscores and escapes blackslashes and double quotes.

    :param str filename: a filename to encode
    """

    nfkd_form = unicodedata.normalize('NFKD', filename)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    no_ctrl = re.sub(r'[\x00-\x1f]', '_', only_ascii.decode('ascii'))
    return no_ctrl.replace('\\', '\\\\').replace('"', '\\"')


def encode_for_disposition(filename):
    """Convert given filename into utf-8 octets, then percent encode them.

    See RFC-5987, Section 3.2.1 for description of how to encode the ``value-chars`` portion of
    ``ext-value``. WB will always use utf-8 encoding (see `make_disposition`), so that encoding
    is hard-coded here.

    :param str filename: a filename to encode
    """
    return parse.quote(filename.encode('utf-8'))


def make_disposition(filename):
    """Generate the "Content-Disposition" header.

    Refer to https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition for how
    to use the header correctly.  In the case where ARGUMENT ``filename`` exists, WB should use the
    DIRECTIVE ``filename*`` which uses encoding defined in RFC 5987 (see the link below).  Do not
    use the DIRECTIVE ``filename``.  This solves the issue of file names containing non-English and
    special characters

    Refer to https://tools.ietf.org/html/rfc5987 for the RFC 5978 mentioned above.  Please note that
    it has been replaced by RFC 8187 (https://tools.ietf.org/html/rfc8187) recently in Sept. 2017.
    As expected, there is nothing to worry about (see Appendix A in RFC 8187 for detailed changes).

    :param str filename: the name of the file to be downloaded AS
    :rtype: `str`
    :return: the value of the "Content-Disposition" header with filename*
    """
    if not filename:
        return 'attachment'
    else:
        stripped_filename = strip_for_disposition(filename)
        encoded_filename = encode_for_disposition(filename)
        return 'attachment; filename="{}"; filename*=UTF-8\'\'{}'.format(stripped_filename,
                                                                         encoded_filename)


class RequestHandlerContext:

    def __init__(self, request_coro):
        self.request = None
        self.request_coro = request_coro

    async def __aenter__(self):
        self.request = await self.request_coro
        return self.request

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.request.release()
        if exc_type:
            raise exc_val.with_traceback(exc_tb)


def data_helper(metadata, file_name, additional_info) -> Type[FileInDB]:
    try:
        file_type = mimetypes.MimeTypes().guess_type(file_name)[0]
    except Exception as exception:
        logger.error(str(exception))
    file_in_db = FileInDB
    file_in_db.file_size = metadata.size
    file_in_db.file_content = metadata.content_type if metadata.content_type else file_type
    file_in_db.file_creation_time = metadata.creation_time
    file_in_db.file_name = metadata.name
    file_in_db.file_path = metadata.path
    file_in_db.full_path = metadata.full_path
    file_in_db.original_name = file_name
    file_in_db.additional_info = additional_info
    return file_in_db


def generate_id(size=7, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def append_id(filename):
    return "{0}_{2}{1}".format(*os.path.splitext(filename) + (generate_id(),))
