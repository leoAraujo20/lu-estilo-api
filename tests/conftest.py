import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import get_async_session
from app.main import app
from app.models import (
    Client,
    Item,
    Order,
    Product,
    ProductSection,
    User,
    table_registry,
)
from app.security import hash_password


@pytest.fixture
def client(session):
    """Cria um cliente de teste para a aplicação FastAPI."""

    def override_get_session():
        return session

    app.dependency_overrides[get_async_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
def engine():
    """Cria um mecanismo de banco de dados assíncrono para testes."""
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    return engine


@pytest_asyncio.fixture
async def session(engine):
    """Cria uma sessão de banco de dados assíncrona para testes."""
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@pytest_asyncio.fixture
async def user(session):
    """Cria um usuário de teste."""
    user = User(username='testuser', password=hash_password('testpassword'))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    user.clean_password = 'testpassword'
    return user


@pytest_asyncio.fixture
async def client_db(session):
    """Cria um cliente de teste."""
    client = Client(
        name='Test Client',
        email='testclient@example.com',
        cpf='12345678901',
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


@pytest_asyncio.fixture
async def product(session):
    """Cria um produto de teste."""
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
    return product


@pytest_asyncio.fixture
async def item(session, product, order):
    """Cria um item de teste."""
    item = Item(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@pytest_asyncio.fixture
async def order(session, client_db, product):
    """Cria um pedido de teste."""
    order = Order(
        client_id=client_db.id,
    )
    order.items.append(
        Item(
            product_id=product.id,
            quantity=2,
        )
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


@pytest.fixture
def token(client, user):
    """Cria um token de acesso para o usuário de teste."""
    user_data = {
        'username': user.username,
        'password': user.clean_password,
    }
    response = client.post('/auth/login', data=user_data)

    token = response.json().get('access_token')
    return token
