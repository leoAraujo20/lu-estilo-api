from http import HTTPStatus

import factory
import pytest

from app.models import Client


class ClientFactory(factory.Factory):
    """Fábrica para criar instâncias de Cliente para testes."""

    class Meta:
        model = Client

    name = factory.Faker('name')
    email = factory.Faker('email')
    cpf = factory.Faker('cpf', locale='pt_BR')


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


def test_create_client_with_existing_email(client, token, client_db):
    """Teste para tentar criar um cliente com email já existente."""
    client_data = {
        'name': 'Duplicate Client',
        'email': client_db.email,
        'cpf': '12345678902',
    }

    response = client.post(
        '/clients/',
        json=client_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Já existe um cliente com este e-mail.'


def test_create_client_with_existing_cpf(client, token, client_db):
    """Teste para tentar criar um cliente com CPF já existente."""
    client_data = {
        'name': 'Duplicate Client',
        'email': 'Duplicate Email',
        'cpf': client_db.cpf,
    }
    response = client.post(
        '/clients/',
        json=client_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Já existe um cliente com este CPF.'


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


def test_get_client_not_found(client, token):
    """Teste para obter um cliente que não existe."""
    response = client.get(
        '/clients/9999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Cliente não encontrado.'


@pytest.mark.asyncio
async def test_get_clients_with_pagination(session, client, token):
    """Teste para obter a lista de clientes com paginação."""
    session.add_all(ClientFactory.build_batch(10))
    await session.commit()

    response = client.get(
        '/clients/?offset=0&limit=5',
        headers={'Authorization': f'Bearer {token}'},
    )
    expected_clients = 5
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['clients']) == expected_clients


@pytest.mark.asyncio
async def test_get_clients_with_name_filter(session, client, token):
    """Teste para obter a lista de clientes filtrando pelo nome."""
    client1 = ClientFactory(name='Alice')
    client2 = ClientFactory(name='Bob')
    session.add_all([client1, client2])
    await session.commit()

    response = client.get(
        '/clients/?name=Alice',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['clients']) == 1


@pytest.mark.asyncio
async def test_get_clients_with_email_filter(session, client, token):
    """Teste para obter a lista de clientes filtrando pelo email."""
    client1 = ClientFactory(email='alice@example.com')
    client2 = ClientFactory(email='bob@example.com')

    session.add_all([client1, client2])
    await session.commit()
    response = client.get(
        '/clients/?email=alice@example.com',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['clients']) == 1


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


def test_update_client_not_found(client, token):
    """Teste para atualizar um cliente que não existe."""
    updated_data = {
        'name': 'Updated Client',
        'email': 'updatedclient@example.com',
    }

    response = client.put(
        '/clients/9999',
        json=updated_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Cliente não encontrado.'


@pytest.mark.asyncio
async def test_update_client_with_existing_email(
    client, token, client_db, session
):
    """Teste para tentar atualizar um cliente com email já existente."""
    existing_client = ClientFactory(email='existing@example.com')
    session.add(existing_client)
    await session.commit()

    updated_data = {
        'name': 'Updated Client',
        'email': existing_client.email,
    }

    response = client.put(
        f'/clients/{client_db.id}',
        json=updated_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Já existe um cliente com este e-mail.'


def test_delete_client(client, token, client_db):
    """Teste para deletar um cliente."""
    response = client.delete(
        f'/clients/{client_db.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_delete_client_not_found(client, token):
    """Teste para tentar deletar um cliente que não existe."""
    response = client.delete(
        '/clients/9999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Cliente não encontrado.'
