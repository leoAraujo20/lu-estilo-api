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
    """Cria um novo cliente."""
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
    """Obtém a lista de clientes."""
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
    """Obtém um cliente pelo ID."""
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
    """Atualiza um cliente pelo ID"""
    client_db = await session.scalar(
        select(Client).where(Client.id == client_id)
    )
    if not client_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cliente não encontrado.',
        )

    existing_client_email = await session.scalar(
        select(Client).where(Client.email == client.email)
    )
    if existing_client_email and existing_client_email.id != client_db.id:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Já existe um cliente com este e-mail.',
        )

    client_db.name = client.name
    client_db.email = client.email

    await session.commit()
    await session.refresh(client_db)

    return client_db


@router.delete('/{client_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_client(client_id: int, session: T_Session) -> None:
    """Deleta um cliente pelo ID."""
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
