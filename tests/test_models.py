import pytest
from sqlalchemy import select

from app.models import (
    Client,
    Item,
    Order,
    OrderStatus,
    Product,
    ProductSection,
    User,
)


@pytest.mark.asyncio
async def test_create_user(session):
    """Testa a criação de um usuário."""
    user = User(username='testuser', password='testpassword')
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user_db = await session.scalar(
        select(User).where(User.username == 'testuser')
    )

    assert user_db
    assert user_db.username == 'testuser'
    assert user_db.password == 'testpassword'
    assert user_db.id == 1


@pytest.mark.asyncio
async def test_create_client(session):
    """Testa a criação de um cliente."""
    client = Client(
        name='Test Client',
        email='testclient@example.com',
        cpf='12345678901',
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)

    client_db = await session.scalar(
        select(Client).where(Client.cpf == '12345678901')
    )

    assert client_db
    assert client_db.name == 'Test Client'
    assert client_db.email == 'testclient@example.com'
    assert client_db.cpf == '12345678901'
    assert client_db.orders == []


@pytest.mark.asyncio
async def test_create_product(session):
    """Testa a criação de um produto."""
    product = Product(
        barcode='1234567890123',
        description='Test Product',
        price_cents=1000,
        section=ProductSection.CLOTHING,
        inventory=10,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    product_db = await session.scalar(
        select(Product).where(Product.barcode == '1234567890123')
    )

    assert product_db
    assert product_db.description == 'Test Product'
    assert product_db.barcode == '1234567890123'
    assert product_db.price_cents == product.price_cents
    assert product_db.section == product.section
    assert product_db.inventory == product.inventory
    assert product_db.expiration_date is None
    assert product_db.items == []


@pytest.mark.asyncio
async def test_create_item(session, product):
    """Testa a criação de um item."""
    item = Item(
        product_id=product.id,
        quantity=2,
    )

    session.add(item)
    await session.commit()
    await session.refresh(item)
    await session.refresh(product)

    item_db = await session.scalar(select(Item).where(Item.id == item.id))

    assert item_db
    assert item_db.product_id == product.id
    assert item_db.product == product
    assert product.items == [item]


@pytest.mark.asyncio
async def test_create_order(session, client_db, item):
    """Testa a criação de um pedido."""
    order = Order(
        client_id=client_db.id,
        items=[item],
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    await session.refresh(client_db)
    await session.refresh(item)

    order_db = await session.scalar(select(Order).where(Order.id == order.id))

    assert order_db
    assert order_db.client_id == client_db.id
    assert order_db.status == OrderStatus.PENDING
    assert order_db.items == [item]
    assert item.order == order
    assert client_db.orders == [order]
