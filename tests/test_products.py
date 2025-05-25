from http import HTTPStatus

import factory

from app.models import Product, ProductSection


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    barcode = factory.Faker('ean13')
    description = factory.Faker('sentence', nb_words=6)
    price_cents = factory.Faker('random_int', min=100, max=10000, step=100)
    section = factory.Iterator(ProductSection)
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


def test_delete_product(client, token, product):
    response = client.delete(
        f'/products/{product.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
