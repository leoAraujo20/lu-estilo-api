from http import HTTPStatus


def test_create_client(client, token):
    """Teste para a criação de um novo cliente."""
    client_data = {
        'name': 'Test Client',
        'email': 'testclient@example.com',
        'cpf': '12345678901',
    }

    response = client.post(
        '/clients/',
        json=client_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'name': 'Test Client',
        'email': 'testclient@example.com',
    }


def test_get_clients(client, token, client_db):
    """Teste para obter a lista de clientes."""
    response = client.get(
        '/clients/',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['clients'] == [
        {
            'id': client_db.id,
            'name': client_db.name,
            'email': client_db.email,
        }
    ]


def test_get_client(client, token, client_db):
    """Teste para obter um cliente pelo ID."""
    response = client.get(
        f'/clients/{client_db.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': client_db.id,
        'name': client_db.name,
        'email': client_db.email,
    }


def test_update_client(client, token, client_db):
    """Teste para atualizar um cliente."""
    updated_data = {
        'name': 'Updated Client',
        'email': 'updatedclient@example.com',
    }

    response = client.put(
        f'/clients/{client_db.id}',
        json=updated_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': client_db.id,
        'name': 'Updated Client',
        'email': 'updatedclient@example.com',
    }


def test_delete_client(client, token, client_db):
    """Teste para deletar um cliente."""
    response = client.delete(
        f'/clients/{client_db.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
