from fastapi import Security, HTTPException
from fastapi.security import APIKeyQuery, APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from authorization.db.crud import get_user_by_key

API_KEY_NAME = "access_api_key"
COOKIE_DOMAIN = "localtest.me"
# api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
user_folder = ""


# api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
        api_key_header: str = Security(api_key_header)
):
    API_KEY = get_user_by_key(api_key_header)['key']
    global user_folder
    user_folder = get_user_by_key(api_key_header)['user_name']
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


def get_user_folder():
    return user_folder

