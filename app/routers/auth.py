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
    """
    Cria um novo usuário.

    Esta rota permite o cadastro de um novo usuário no sistema.
    O nome de usuário deve ser único.

    Args:
        user (UserSchema):
            - Dados do usuário a ser criado (username e password).
        session:
             - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        UserPublic:
           - Dados públicos do usuário criado(id, username).

    Raises:
        HTTPException:
             - 409 CONFLICT se o usuário já existir.

    Example:
        Request:
            POST /auth/register
            {
                "username": "usuario1",
                "password": "senha123"
            }
        Response:
            {
                "id": 1,
                "username": "usuario1"
            }
    """

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
    """
    Autentica um usuário e gera um token JWT.

    Esta rota realiza a autenticação de um usuário a partir do
    username e password, retornando um token JWT para acesso autenticado.

    Args:
        user (OAuth2PasswordRequestForm):
            - Formulário OAuth2 com username e password.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        TokenSchema:
            - Token JWT de acesso e tipo do token.

    Raises:
        HTTPException:
            - 401 UNAUTHORIZED se as credenciais forem inválidas.

    Example:
        Request (form-data):
            POST /auth/login
            username=usuario1
            password=senha123
        Response:
            {
                "access_token": "<jwt_token>",
                "token_type": "bearer"
            }
    """

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
    """
    Atualiza o token JWT do usuário autenticado.

    Esta rota permite renovar o token JWT de um usuário já autenticado.

    Args:
        user (User):
            - Usuário autenticado extraído do token atual.

    Returns:
        TokenSchema:
             - Novo token JWT de acesso e tipo do token.

    Example:
        Request (header):
            POST /auth/refresh-token
            Authorization: Bearer <jwt_token>
        Response:
            {
                "access_token": "<novo_jwt_token>",
                "token_type": "bearer"
            }
    """

    access_token = create_jwt_token(data={'sub': user.username})
    return {
        'access_token': access_token,
        'token_type': 'bearer',
    }
