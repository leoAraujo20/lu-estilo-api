from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: int
    username: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
