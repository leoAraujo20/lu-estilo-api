from http import HTTPStatus
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import Product
from app.schemas import (
    ProductFilter,
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
    """
    Cria um novo produto.

    Esta rota permite o cadastro de um novo produto no sistema.
    O código de barras deve ser único.

    Args:
        session:
            - Sessão de banco de dados injetada pelo FastAPI.
        product (ProductSchema):
            - Dados do produto a ser criado (
                barcode,
                description,
                price_cents,
                section(clothing, shoes, accessories),
                inventory,
                expiration_date(default None)
            ).

    Returns:
        ProductPublic:
            - Dados públicos do produto criado.

    Raises:
        HTTPException:
            - 409 CONFLICT se já existir produto com o mesmo código de barras.

    Example:
        Request:
            POST /products/
            {
                "barcode": "123456789",
                "description": "Produto Exemplo",
                "price_cents": 1000,
                "section": "clothing",
                "inventory": 10,
                "expiration_date": "2024-12-31"
            }
        Response:
            {
                "id": 1,
                "barcode": "123456789",
                "description": "Produto Exemplo",
                "price_cents": 1000,
                "section": "clothing",
                "inventory": 10,
                "expiration_date": "2024-12-31"
            }
    """
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
async def get_products(
    session: T_Session, filter_query: Annotated[ProductFilter, Query()]
) -> ProductList:
    """
    Obtém a lista de produtos.

    Esta rota retorna uma lista paginada de produtos,
    podendo ser filtrada por seção, preço máximo e inventário mínimo.

    Args:
        session:
            - Sessão de banco de dados injetada pelo FastAPI.
        filter_query (ProductFilter):
            - Parâmetros de filtro e paginação (
                limit, offset, section, price_cents, inventory
            ).

    Returns:
        ProductList:
            - Lista de produtos.

    Example:
        Request:
            GET /products/?limit=10&offset=0&section=clothing
        Response:
            {
                "products": [
                    {
                        "id": 1,
                        "barcode": "123456789",
                        "description": "Produto Exemplo",
                        "price_cents": 1000,
                        "section": "clothing",
                        "inventory": 10,
                        "expiration_date": "2024-12-31"
                    }
                ]
            }
    """
    query = (
        select(Product).offset(filter_query.offset).limit(filter_query.limit)
    )

    if filter_query.section:
        query = query.where(Product.section == filter_query.section)
    if filter_query.price_cents:
        query = query.where(Product.price_cents <= filter_query.price_cents)
    if filter_query.inventory:
        query = query.where(Product.inventory >= filter_query.inventory)

    products = await session.scalars(query)
    products_list = products.all()
    return {'products': products_list}


@router.get(
    '/{product_id}', response_model=ProductPublic, status_code=HTTPStatus.OK
)
async def get_product(product_id: int, session: T_Session) -> ProductPublic:
    """
    Obtém um produto pelo ID.

    Esta rota retorna os dados de um produto específico a partir do seu ID.

    Args:
        product_id (int):
            - ID do produto.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        ProductPublic:
            - Dados públicos do produto.

    Raises:
        HTTPException:
            - 404 NOT FOUND se o produto não existir.

    Example:
        Request:
            GET /products/1
        Response:
            {
                "id": 1,
                "barcode": "123456789",
                "description": "Produto Exemplo",
                "price_cents": 1000,
                "section": "clothing",
                "inventory": 10,
                "expiration_date": "2024-12-31"
            }
    """
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
    """
    Atualiza um produto pelo ID.

    Esta rota permite atualizar os dados de um produto existente.

    Args:
        product_id (int):
            - ID do produto.
        product (ProductUpdate):
            - Dados a serem atualizados (
                description,
                price_cents,
                section(clothing, shoes, accessories),
                inventory,
                expiration_date
            ).
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        ProductPublic:
            - Dados públicos do produto atualizado.

    Raises:
        HTTPException:
            - 404 NOT FOUND se o produto não existir.

    Example:
        Request:
            PUT /products/1
            {
                "description": "Novo Produto",
                "price_cents": 1500
            }
        Response:
            {
                "id": 1,
                "barcode": "123456789",
                "description": "Novo Produto",
                "price_cents": 1500,
                "section": "clothing",
                "inventory": 10,
                "expiration_date": "2024-12-31"
            }
    """
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
    """
    Remove um produto pelo ID.

    Esta rota remove um produto do sistema a partir do seu ID.

    Args:
        product_id (int):
            - ID do produto.
        session:
            - Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        None

    Raises:
        HTTPException:
            - 404 NOT FOUND se o produto não existir.

    Example:
        Request:
            DELETE /products/1
        Response:
            Status 204 No Content
    """
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
