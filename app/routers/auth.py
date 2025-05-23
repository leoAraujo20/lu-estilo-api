from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.database import get_async_session
from app.models import User
from app.schemas import TokenSchema, UserPublic, UserSchema
from app.security import (
    create_jwt_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post(
    '/register', status_code=HTTPStatus.CREATED, response_model=UserPublic
)
async def create_user(user: UserSchema, session=Depends(get_async_session)):
    """Rota para criar um novo usuário."""

    user_db = await session.scalar(
        select(User).where(User.username == user.username)
    )

    if user_db:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='O usuário já existe.',
        )

    user = User(username=user.username, password=hash_password(user.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post('/login', status_code=HTTPStatus.OK, response_model=TokenSchema)
async def login_for_access_token(
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    session=Depends(get_async_session),
):
    """Rota para autenticar um usuário e gerar um token JWT."""
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Usuário ou senha inválidos.',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    user_db = await session.scalar(
        select(User).where(User.username == user.username)
    )

    if not user_db:
        raise credentials_exception

    if not verify_password(user.password, user_db.password):
        raise credentials_exception

    access_token = create_jwt_token(data={'sub': user_db.username})

    return {
        'access_token': access_token,
        'token_type': 'bearer',
    }


@router.post(
    '/refresh-token', status_code=HTTPStatus.OK, response_model=TokenSchema
)
async def refresh_token(user: Annotated[User, Depends(get_current_user)]):
    """Rota para atualizar o token JWT."""
    access_token = create_jwt_token(data={'sub': user.username})
    return {
        'access_token': access_token,
        'token_type': 'bearer',
    }
