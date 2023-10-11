from fastapi import APIRouter, HTTPException
from starlette import status

from authorization.db.crud import User, get_key_per_user
from authorization.models.structures import UserInDB

router = APIRouter()


@router.post("/create_account")
async def create_account(user: UserInDB) -> dict:
    """
    create user in database
    :param user: user information
    :return: success or fail
    """
    file_handler_user = User(user)
    created = User.create(file_handler_user)
    return created


@router.get("/get_api_key")
async def metadata(user_name: str = None, password: str = None) -> dict or HTTPException:
    """
    by providing you user name and password can get using this endpoint the api key associated to you
    :param user_name: the user name used to get the api key
    :param password: the user passport
    :return: dict that contains the user api key {'api_key': response['key']}
    """
    api_key = get_key_per_user(user_name, password)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='no api key found for this user'
        )
    return api_key

