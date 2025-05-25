from http import HTTPStatus


def test_create_order(client, token, client_db, product):
    order_data = {
        'client_id': client_db.id,
        'items': [
            {'product_id': product.id, 'quantity': 2},
        ],
    }

    response = client.post(
        '/orders/',
        json=order_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'client_id': client_db.id,
        'items': [
            {'product_id': product.id, 'quantity': 2},
        ],
        'status': 'pending',
        'order_date': response.json().get('order_date'),
    }


def test_get_orders(client, token, order):
    response = client.get(
        '/orders/',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'orders': [
            {
                'id': order.id,
                'client_id': order.client_id,
                'items': [
                    {
                        'product_id': order.items[0].product_id,
                        'quantity': order.items[0].quantity,
                    }
                ],
                'status': order.status.value,
                'order_date': response.json()['orders'][0].get('order_date'),
            }
        ],
    }


def test_get_order(client, token, order):
    response = client.get(
        f'/orders/{order.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': order.id,
        'client_id': order.client_id,
        'items': [
            {
                'product_id': order.items[0].product_id,
                'quantity': order.items[0].quantity,
            }
        ],
        'status': order.status.value,
        'order_date': response.json().get('order_date'),
    }


def test_update_order(client, token, order):
    update_data = {
        'status': 'shipped',
    }

    response = client.put(
        f'/orders/{order.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': order.id,
        'client_id': order.client_id,
        'items': [
            {
                'product_id': order.items[0].product_id,
                'quantity': order.items[0].quantity,
            }
        ],
        'status': 'shipped',
        'order_date': response.json().get('order_date'),
    }
