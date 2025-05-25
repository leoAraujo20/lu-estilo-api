from http import HTTPStatus
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import Client, Item, Order, Product
from app.schemas import OrderList, OrderPublic, OrderSchema, OrderUpdate
from app.security import get_current_user

router = APIRouter(
    prefix='/orders',
    tags=['orders'],
    dependencies=[Depends(get_current_user)],
)

T_Session = Annotated[AsyncGenerator[AsyncSession], Depends(get_async_session)]


@router.post('/', response_model=OrderPublic, status_code=HTTPStatus.CREATED)
async def create_order(order: OrderSchema, session: T_Session) -> OrderPublic:
    """Cria um novo pedido."""
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
async def get_orders(session: T_Session) -> OrderList:
    """Obtém a lista de pedidos."""
    orders = await session.scalars(select(Order))
    orders_list = orders.all()
    return {'orders': orders_list}


@router.get(
    '/{order_id}', response_model=OrderPublic, status_code=HTTPStatus.OK
)
async def get_order(order_id: int, session: T_Session) -> OrderPublic:
    """Obtém um pedido específico pelo ID."""
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
    """Atualiza um pedido existente."""
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
    """Remove um pedido existente."""
    order_db = await session.scalar(select(Order).where(Order.id == order_id))
    if not order_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Pedido não encontrado.',
        )

    await session.delete(order_db)
    await session.commit()
