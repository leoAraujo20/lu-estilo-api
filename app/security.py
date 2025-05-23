from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, PyJWTError
from pwdlib import PasswordHash
from sqlalchemy import select

from app.database import get_async_session
from app.models import User
from app.settings import Settings

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def hash_password(password: str) -> str:
    """Cria um hash seguro para a senha fornecida."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return password_hash.verify(plain_password, hashed_password)


def create_jwt_token(data: dict) -> str:
    """Cria um token JWT com os dados fornecidos."""
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=Settings().ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update({'exp': expire})

    encoded_jwt = jwt.encode(
        payload, Settings().SECRET_KEY, algorithm=Settings().ALGORITHM
    )

    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session=Depends(get_async_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Credenciais inválidas',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(
            token, Settings().SECRET_KEY, algorithms=[Settings().ALGORITHM]
        )
        username_payload = payload.get('sub')

        if username_payload is None:
            raise credentials_exception

    except ExpiredSignatureError:
        credentials_exception.detail = 'Token expirado'
        raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user_db = await session.scalar(
        select(User).where(User.username == username_payload)
    )

    if user_db is None:
        raise credentials_exception

    return user_db
