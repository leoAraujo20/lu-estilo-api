from http import HTTPStatus
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import Client
from app.schemas import (
    ClientList,
    ClientPublic,
    ClientSchema,
    ClientUpdate,
    FilterClient,
)
from app.security import get_current_user

router = APIRouter(
    prefix='/clients',
    tags=['clients'],
    dependencies=[Depends(get_current_user)],
)

T_Session = Annotated[AsyncGenerator[AsyncSession], Depends(get_async_session)]


@router.post('/', response_model=ClientPublic, status_code=HTTPStatus.CREATED)
async def create_client(
    client: ClientSchema, session: T_Session
) -> ClientPublic:
    """
    Cria um novo cliente.

    Esta rota permite o cadastro de um novo cliente no sistema.
    O e-mail e o CPF devem ser únicos.

    Args:
        client (ClientSchema):
            - Dados do cliente a ser criado (name, email, cpf).
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        ClientPublic:
            - Dados públicos do cliente criado(id, name, email).

    Raises:
        HTTPException:
            - 409 CONFLICT se já existir cliente com o mesmo e-mail ou CPF.

    Example:
        Request:
            POST /clients/
            {
                "name": "Maria Silva",
                "email": "maria@email.com",
                "cpf": "12345678900"
            }
        Response:
            {
                "id": 1,
                "name": "Maria Silva",
                "email": "maria@email.com",
            }
    """
    client_db = await session.scalar(
        select(Client).where(
            (Client.cpf == client.cpf) | (Client.email == client.email)
        )
    )
    if not client_db:
        client_db = Client(
            name=client.name,
            email=client.email,
            cpf=client.cpf,
        )
        session.add(client_db)
        await session.commit()
        await session.refresh(client_db)
        return client_db

    if client.email == client_db.email:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Já existe um cliente com este e-mail.',
        )
    if client.cpf == client_db.cpf:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Já existe um cliente com este CPF.',
        )


@router.get('/', response_model=ClientList)
async def get_clients(
    session: T_Session, filter_query: Annotated[FilterClient, Query()]
) -> ClientList:
    """
    Obtém a lista de clientes.

    Esta rota retorna uma lista paginada de clientes,
    podendo ser filtrada por nome ou e-mail.

    Args:
        session:
            - Sessão de banco de dados injetada pelo FastAPI.
        filter_query (FilterClient):
            - Parâmetros de filtro e paginação (limit, offset, name, email).

    Returns:
        ClientList:
            - Lista de clientes(id, name, email).

    Example:
        Request:
            GET /clients/?limit=10&offset=0&name=Maria
        Response:
            {
                "clients": [
                    {
                        "id": 1,
                        "name": "Maria Silva",
                        "email": "maria@email.com",
                    }
                ]
            }
    """
    query = (
        select(Client).offset(filter_query.offset).limit(filter_query.limit)
    )

    if filter_query.name:
        query = query.filter(Client.name.contains(filter_query.name))
    if filter_query.email:
        query = query.filter(Client.email.contains(filter_query.email))

    clients = await session.scalars(query)
    clients_list = clients.all()

    return {'clients': clients_list}


@router.get(
    '/{client_id}', response_model=ClientPublic, status_code=HTTPStatus.OK
)
async def get_client(client_id: int, session: T_Session) -> ClientPublic:
    """
    Obtém um cliente pelo ID.

    Esta rota retorna os dados de um cliente específico a partir do seu ID.

    Args:
        client_id (int):
            - ID do cliente.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        ClientPublic:
            - Dados públicos do cliente(id, name, email).

    Raises:
        HTTPException:
            - 404 NOT FOUND se o cliente não existir.

    Example:
        Request:
            GET /clients/1
        Response:
            {
                "id": 1,
                "name": "Maria Silva",
                "email": "maria@email.com",
            }
    """
    client = await session.scalar(select(Client).where(Client.id == client_id))
    if not client:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cliente não encontrado.',
        )
    return client


@router.put(
    '/{client_id}', response_model=ClientPublic, status_code=HTTPStatus.OK
)
async def update_client(
    client_id: int, client: ClientUpdate, session: T_Session
) -> ClientPublic:
    """
    Atualiza um cliente pelo ID.

    Esta rota permite atualizar os dados de um cliente existente.

    Args:
        client_id (int):
            - ID do cliente.
        client (ClientUpdate):
            - Dados a serem atualizados(name, email).
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        ClientPublic:
            - Dados públicos do cliente atualizado(id, name, email).

    Raises:
        HTTPException:
            - 404 NOT FOUND se o cliente não existir.
        HTTPException:
            - 409 CONFLICT se o e-mail já estiver em uso por outro cliente.

    Example:
        Request:
            PUT /clients/1
            {
                "name": "Maria Souza"
            }
        Response:
            {
                "id": 1,
                "name": "Maria Souza",
                "email": "maria@email.com",
            }
    """
    client_db = await session.scalar(
        select(Client).where(Client.id == client_id)
    )
    if not client_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cliente não encontrado.',
        )

    update_data = client.model_dump(exclude_unset=True)
    if 'email' in update_data:
        existing_client = await session.scalar(
            select(Client).where(Client.email == update_data['email'])
        )
        if existing_client and existing_client.id != client_id:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Já existe um cliente com este e-mail.',
            )

    for field, value in update_data.items():
        setattr(client_db, field, value)

    await session.commit()
    await session.refresh(client_db)
    return client_db


@router.delete('/{client_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_client(client_id: int, session: T_Session) -> None:
    """
    Deleta um cliente pelo ID.

    Esta rota remove um cliente do sistema a partir do seu ID.

    Args:
        client_id (int):
            - ID do cliente.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        None

    Raises:
        HTTPException:
            - 404 NOT FOUND se o cliente não existir.

    Example:
        Request:
            DELETE /clients/1
        Response:
            Status 204 No Content
    """
    client_db = await session.scalar(
        select(Client).where(Client.id == client_id)
    )
    if not client_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cliente não encontrado.',
        )

    await session.delete(client_db)
    await session.commit()
