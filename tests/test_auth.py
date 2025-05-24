from http import HTTPStatus


def test_create_user(client):
    """Teste para a criação de um novo usuário."""
    user_data = {
        'username': 'testuser',
        'password': 'testpassword'
    }

    response = client.post('/auth/register', json=user_data)

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'username': 'testuser',
    }


def test_create_user_already_exists(client, user):
    """Teste para tentar criar um usuário que já existe."""
    user_data = {
        'username': user.username,
        'password': 'testpassword'
    }

    response = client.post('/auth/register', json=user_data)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        'detail': 'O usuário já existe.'
    }


def test_login_for_access_token(client, user):
    """Teste para o login e obtenção do token de acesso."""
    login_data = {
        'username': user.username,
        'password': user.clean_password
    }

    response = client.post('/auth/login', data=login_data)

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json()
    assert response.json()['token_type'] == 'bearer'


def test_login_for_access_token_nonexistent_user(client, user):
    """Teste para tentar fazer login com um usuário que não existe."""
    login_data = {
        'username': 'nonexistentuser',
        'password': 'testpassword'
    }

    response = client.post('/auth/login', data=login_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        'detail': 'Usuário ou senha inválidos.'
    }


def test_login_for_access_token_incorrect_password(client, user):
    """Teste para tentar fazer login com uma senha incorreta."""
    login_data = {
        'username': user.username,
        'password': 'incorrectpassword'
    }

    response = client.post('/auth/login', data=login_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        'detail': 'Usuário ou senha inválidos.'
    }


def test_refresh_token(client, user):
    """Teste para a atualização do token de acesso."""
    login_data = {
        'username': user.username,
        'password': user.clean_password
    }

    response = client.post('/auth/login', data=login_data)

    assert response.status_code == HTTPStatus.OK

    token = response.json()['access_token']

    response = client.post(
        '/auth/refresh-token',
        headers={'Authorization': f"Bearer {token}"}
    )

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json()
    assert response.json()['token_type'] == 'bearer'
