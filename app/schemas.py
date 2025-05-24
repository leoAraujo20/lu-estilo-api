from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: int
    username: str


class ClientSchema(BaseModel):
    name: str
    email: str
    cpf: str


class ClientPublic(BaseModel):
    id: int
    name: str
    email: str


class ClientUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class ClientList(BaseModel):
    clients: list[ClientPublic]


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class FilterPage(BaseModel):
    offset: int = 0
    limit: int = 10


class FilterClient(FilterPage):
    name: str | None = None
    email: str | None = None
