from http import HTTPStatus

import factory
import factory.fuzzy
import pytest

from app.models import Product, ProductSection


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    barcode = factory.Faker('ean13')
    description = factory.Faker('sentence', nb_words=6)
    price_cents = factory.Faker('random_int', min=100, max=10000, step=100)
    section = factory.fuzzy.FuzzyChoice(ProductSection)
    inventory = factory.Faker('random_int', min=0, max=1000)
    expiration_date = None


def test_create_product(client, token):
    product_data = {
        'barcode': '1234567890123',
        'description': 'This is a test product.',
        'price_cents': 1999,
        'section': ProductSection.CLOTHING.value,
        'inventory': 100,
    }

    response = client.post(
        '/products/',
        json=product_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'barcode': '1234567890123',
        'description': 'This is a test product.',
        'price_cents': 1999,
        'section': ProductSection.CLOTHING.value,
        'inventory': 100,
        'expiration_date': None,
    }


def test_create_product_with_existing_barcode(client, token, product):
    product_data = {
        'barcode': product.barcode,
        'description': 'This is another test product.',
        'price_cents': 2999,
        'section': ProductSection.CLOTHING.value,
        'inventory': 50,
    }

    response = client.post(
        '/products/',
        json=product_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert (
        response.json()['detail']
        == 'Já existe um produto com este código de barras.'
    )


def test_get_products(client, token, product):
    response = client.get(
        '/products/',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'products': [
            {
                'id': product.id,
                'barcode': product.barcode,
                'description': product.description,
                'price_cents': product.price_cents,
                'section': ProductSection.CLOTHING.value,
                'inventory': product.inventory,
                'expiration_date': product.expiration_date,
            }
        ]
    }


def test_get_product_not_found(client, token, product):
    response = client.get(
        '/products/9999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Produto não encontrado.'}


@pytest.mark.asyncio
async def test_get_products_with_pagination(client, token, session):
    session.add_all(ProductFactory.build_batch(10))
    await session.commit()

    response = client.get(
        '/products/?offset=0&limit=5',
        headers={'Authorization': f'Bearer {token}'},
    )
    expected_products = 5

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['products']) == expected_products


@pytest.mark.asyncio
async def test_get_products_with_section_filter(client, token, session):
    session.add_all(
        ProductFactory.build_batch(10, section=ProductSection.SHOES)
    )
    clothing_products = ProductFactory.build_batch(
        2, section=ProductSection.CLOTHING
    )
    session.add_all(clothing_products)
    await session.commit()

    response = client.get(
        '/products/?section=clothing',
        headers={'Authorization': f'Bearer {token}'},
    )

    expected_products = 2
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['products']) == expected_products


@pytest.mark.asyncio
async def test_get_products_with_price_cents_filter(client, token, session):
    session.add_all(ProductFactory.build_batch(10, price_cents=30000))
    clothing_products = ProductFactory.build_batch(2, price_cents=20000)
    session.add_all(clothing_products)
    await session.commit()

    response = client.get(
        '/products/?price_cents=20000',
        headers={'Authorization': f'Bearer {token}'},
    )

    expected_products = 2
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['products']) == expected_products


@pytest.mark.asyncio
async def test_get_products_with_inventory_filter(client, token, session):
    session.add_all(ProductFactory.build_batch(10, inventory=100))
    clothing_products = ProductFactory.build_batch(2, inventory=200)
    session.add_all(clothing_products)
    await session.commit()

    response = client.get(
        '/products/?inventory=200',
        headers={'Authorization': f'Bearer {token}'},
    )

    expected_products = 2
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['products']) == expected_products


def test_get_product(client, token, product):
    response = client.get(
        f'/products/{product.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': product.id,
        'barcode': product.barcode,
        'description': product.description,
        'price_cents': product.price_cents,
        'section': ProductSection.CLOTHING.value,
        'inventory': product.inventory,
        'expiration_date': product.expiration_date,
    }


def test_update_product(client, token, product):
    update_data = {
        'description': 'Updated product description.',
        'price_cents': 2999,
        'inventory': 50,
    }

    response = client.put(
        f'/products/{product.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': product.id,
        'barcode': product.barcode,
        'description': 'Updated product description.',
        'price_cents': 2999,
        'section': ProductSection.CLOTHING.value,
        'inventory': 50,
        'expiration_date': product.expiration_date,
    }


def test_update_product_not_found(client, token, product):
    update_data = {
        'description': 'Updated product description.',
        'price_cents': 2999,
        'inventory': 50,
    }

    response = client.put(
        '/products/9999',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Produto não encontrado.'}


def test_delete_product(client, token, product):
    response = client.delete(
        f'/products/{product.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_delete_product_not_found(client, token, product):
    response = client.delete(
        '/products/9999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Produto não encontrado.'}
