from http import HTTPStatus
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import Client, Item, Order, Product
from app.schemas import (
    OrderFilter,
    OrderList,
    OrderPublic,
    OrderSchema,
    OrderUpdate,
)
from app.security import get_current_user

router = APIRouter(
    prefix='/orders',
    tags=['orders'],
    dependencies=[Depends(get_current_user)],
)

T_Session = Annotated[AsyncGenerator[AsyncSession], Depends(get_async_session)]


@router.post('/', response_model=OrderPublic, status_code=HTTPStatus.CREATED)
async def create_order(order: OrderSchema, session: T_Session) -> OrderPublic:
    """
    Cria um novo pedido.

    Esta rota permite o cadastro de um novo pedido no sistema.
    O pedido deve conter um cliente válido e uma lista de itens com produtos
    existentes e estoque suficiente.

    Args:
        order (OrderSchema):
            - Dados do pedido a ser criado:
                - client_id (int): ID do cliente.
                - items (list[ItemSchema]): Lista de itens.
                - status (OrderStatus): Status do pedido (default: PENDING).
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        OrderPublic:
            - Dados públicos do pedido criado:
                - id (int)
                - client_id (int)
                - items (list[ItemSchema])
                - status (OrderStatus)
                - order_date (datetime)

    Raises:
        HTTPException:
            - 404 NOT FOUND se o cliente ou algum produto não existir.
            - 400 BAD REQUEST se não houver estoque.

    Example:
        Request:
            POST /orders/
            {
                "client_id": 1,
                "items": [
                    {"product_id": 2, "quantity": 3}
                ],
                "status": "PENDING"
            }
        Response:
            {
                "id": 10,
                "client_id": 1,
                "items": [
                    {"product_id": 2, "quantity": 3}
                ],
                "status": "PENDING",
                "order_date": "2024-06-01T12:00:00"
            }
    """
    client_db = await session.scalar(
        select(Client).where(Client.id == order.client_id)
    )
    if not client_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cliente não encontrado.',
        )

    new_order = Order(
        client_id=order.client_id,
        status=order.status,
    )
    await session.flush()

    items = []
    for item in order.items:
        product_db = await session.scalar(
            select(Product).where(Product.id == item.product_id)
        )
        if not product_db:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Produto com ID {item.product_id} não encontrado.',
            )

        if product_db.inventory < item.quantity:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'Estoque insuficiente para o produto {product_db.id}.',
            )

        items.append(
            Item(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
            )
        )

    new_order.items = items
    session.add(new_order)
    await session.commit()
    await session.refresh(new_order)
    return new_order


@router.get('/', response_model=OrderList, status_code=HTTPStatus.OK)
async def get_orders(
    session: T_Session, filter_query: Annotated[OrderFilter, Query()]
) -> OrderList:
    """
    Obtém a lista de pedidos.

    Esta rota retorna uma lista paginada de pedidos,
    podendo ser filtrada por cliente, status,
    data de pedido e seção do produto.

    Args:
        session:
            - Sessão de banco de dados injetada pelo FastAPI.
        filter_query (OrderFilter):
            - Parâmetros de filtro e paginação:
                - limit (int), offset (int)
                - client_id (int, opcional)
                - status (OrderStatus, opcional)
                - order_date_from (datetime, opcional)
                - order_date_to (datetime, opcional)
                - product_section (ProductSection, opcional)

    Returns:
        OrderList:
            - Lista de pedidos:
                - orders (list[OrderPublic])

    Example:
        Request:
            GET /orders/?limit=10&offset=0&client_id=1
        Response:
            {
                "orders": [
                    {
                        "id": 10,
                        "client_id": 1,
                        "items": [
                            {"product_id": 2, "quantity": 3}
                        ],
                        "status": "PENDING",
                        "order_date": "2024-06-01T12:00:00"
                    }
                ]
            }
    """
    query = select(Order).offset(filter_query.offset).limit(filter_query.limit)

    if filter_query.client_id:
        query = query.where(Order.client_id == filter_query.client_id)
    if filter_query.status:
        query = query.where(Order.status == filter_query.status)
    if filter_query.order_date_from:
        query = query.where(Order.order_date >= filter_query.order_date_from)
    if filter_query.order_date_to:
        query = query.where(Order.order_date <= filter_query.order_date_to)

    orders = await session.scalars(query)
    orders_list = orders.all()
    return {'orders': orders_list}


@router.get(
    '/{order_id}', response_model=OrderPublic, status_code=HTTPStatus.OK
)
async def get_order(order_id: int, session: T_Session) -> OrderPublic:
    """
    Obtém um pedido específico pelo ID.

    Esta rota retorna os dados de um pedido específico a partir do seu ID.

    Args:
        order_id (int):
            - ID do pedido.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        OrderPublic:
            - Dados públicos do pedido:
                - id (int)
                - client_id (int)
                - items (list[ItemSchema])
                - status (OrderStatus)
                - order_date (datetime)

    Raises:
        HTTPException:
            - 404 NOT FOUND se o pedido não existir.

    Example:
        Request:
            GET /orders/10
        Response:
            {
                "id": 10,
                "client_id": 1,
                "items": [
                    {"product_id": 2, "quantity": 3}
                ],
                "status": "PENDING",
                "order_date": "2024-06-01T12:00:00"
            }
    """
    order_db = await session.scalar(select(Order).where(Order.id == order_id))
    if not order_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Pedido não encontrado.',
        )
    return order_db


@router.put(
    '/{order_id}', response_model=OrderPublic, status_code=HTTPStatus.OK
)
async def update_order(
    order_id: int, order: OrderUpdate, session: T_Session
) -> OrderPublic:
    """
    Atualiza um pedido existente.

    Esta rota permite atualizar o status de um pedido existente.

    Args:
        order_id (int):
            - ID do pedido.
        order (OrderUpdate):
            - Dados a serem atualizados:
                - status (OrderStatus, opcional)
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        OrderPublic:
            - Dados públicos do pedido atualizado:
                - id (int)
                - client_id (int)
                - items (list[ItemSchema])
                - status (OrderStatus)
                - order_date (datetime)

    Raises:
        HTTPException:
            - 404 NOT FOUND se o pedido não existir.

    Example:
        Request:
            PUT /orders/10
            {
                "status": "COMPLETED"
            }
        Response:
            {
                "id": 10,
                "client_id": 1,
                "items": [
                    {"product_id": 2, "quantity": 3}
                ],
                "status": "COMPLETED",
                "order_date": "2024-06-01T12:00:00"
            }
    """
    order_db = await session.scalar(select(Order).where(Order.id == order_id))
    if not order_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Pedido não encontrado.',
        )

    if order.status:
        order_db.status = order.status

    await session.commit()
    await session.refresh(order_db)
    return order_db


@router.delete('/{order_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_order(order_id: int, session: T_Session) -> None:
    """
    Remove um pedido existente.

    Esta rota remove um pedido do sistema a partir do seu ID.

    Args:
        order_id (int):
            - ID do pedido.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        None

    Raises:
        HTTPException:
            - 404 NOT FOUND se o pedido não existir.

    Example:
        Request:
            DELETE /orders/10
        Response:
            Status 204 No Content
    """
    order_db = await session.scalar(select(Order).where(Order.id == order_id))
    if not order_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Pedido não encontrado.',
        )

    await session.delete(order_db)
    await session.commit()
