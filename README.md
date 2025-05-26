# Lu Estilo API

API para gerenciamento de usuarios, clientes, produtos e pedidos.

## Pré-requisitos

- [Python 3.13](https://www.python.org/downloads/)
- [uv (gerenciador de pacotes)](https://github.com/astral-sh/uv)
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Passos para rodar localmente

1. **Clone o repositorio:**

   ```sh
   git clone https://github.com/leoAraujo20/lu-estilo-api.git
   ```

2. **Instale o `uv` (se ainda não tiver):**

   ```sh
   pip install uv
   ```

3. **Crie um ambiente virtual**

   ```sh
    uv venv
   ```

4. **Ativar o ambiente virtual**

   ```sh
    .venv\Scripts\activate # Windows
    .venv/bin/activate # Linux e mac
   ```

5. **Crie o arquivo `.env` na raiz do projeto com suas próprias configurações:**

   ```sh
   SECRET_KEY="sua_chave_secreta"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   DATABASE_URL="postgresql+psycopg://app_user:senha@lu_estilo_database:5432/nome_do_banco"
   POSTGRES_USER="app_user" # Mantenha como app_user
   POSTGRES_PASSWORD="senha"
   POSTGRES_DB="nome_do_banco"
   ```

6. **Instale as depedências do projeto:**

   ```sh
    uv sync
   ```

7. **Ajuste o final de linha do arquivo `entrypoint.sh` (importante para usuários Windows):**

   Após clonar o repositório, verifique se o arquivo `entrypoint.sh` está com final de linha do tipo **LF** (Line Feed).  
   Se estiver como **CRLF**, troque para **LF** no VS Code (canto inferior direito) e salve o arquivo.  
   Isso evita erros de execução no Docker/Linux.

8. **Execute o docker compose:**

   ```sh
   docker compose up --build
   ```

9. **Acesse a aplicação:**

- Documentação Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
