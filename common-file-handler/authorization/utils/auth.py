
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_password_hash(password: str) -> str:
    """
    hash password
    :param password: password
    :return: hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    verify password
    :param plain_password: password entered by user
    :param hashed_password: hashed password
    :return: True or False
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_key():
    return secrets.token_urlsafe(16)
