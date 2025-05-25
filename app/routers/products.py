from http import HTTPStatus
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import Product
from app.schemas import (
    ProductList,
    ProductPublic,
    ProductSchema,
    ProductUpdate,
)
from app.security import get_current_user

T_Session = Annotated[AsyncGenerator[AsyncSession], Depends(get_async_session)]

router = APIRouter(
    prefix='/products',
    tags=['products'],
    dependencies=[Depends(get_current_user)],
)


@router.post('/', response_model=ProductPublic, status_code=HTTPStatus.CREATED)
async def create_product(
    session: T_Session, product: ProductSchema
) -> ProductPublic:
    """Cria um novo produto."""
    product_db = await session.scalar(
        select(Product).where(Product.barcode == product.barcode)
    )
    if product_db:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Já existe um produto com este código de barras.',
        )

    product = Product(
        barcode=product.barcode,
        description=product.description,
        price_cents=product.price_cents,
        section=product.section,
        inventory=product.inventory,
        expiration_date=product.expiration_date,
    )

    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


@router.get('/', response_model=ProductList, status_code=HTTPStatus.OK)
async def get_products(session: T_Session) -> ProductList:
    """Obtém a lista de produtos."""
    products = await session.scalars(select(Product))
    products_list = products.all()
    return {'products': products_list}


@router.get(
    '/{product_id}', response_model=ProductPublic, status_code=HTTPStatus.OK
)
async def get_product(product_id: int, session: T_Session) -> ProductPublic:
    """Obtém um produto pelo ID."""
    product_db = await session.scalar(
        select(Product).where(Product.id == product_id)
    )
    if not product_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Produto não encontrado.',
        )

    return product_db


@router.put(
    '/{product_id}', response_model=ProductPublic, status_code=HTTPStatus.OK
)
async def update_product(
    product_id: int, product: ProductUpdate, session: T_Session
) -> ProductPublic:
    """Atualiza um produto pelo ID."""
    product_db = await session.scalar(
        select(Product).where(Product.id == product_id)
    )
    if not product_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Produto não encontrado.',
        )

    for field, value in product.model_dump(exclude_unset=True).items():
        setattr(product_db, field, value)

    await session.commit()
    await session.refresh(product_db)
    return product_db


@router.delete('/{product_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_product(product_id: int, session: T_Session) -> None:
    """Remove um produto pelo ID."""
    product_db = await session.scalar(
        select(Product).where(Product.id == product_id)
    )
    if not product_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Produto não encontrado.',
        )

    await session.delete(product_db)
    await session.commit()
