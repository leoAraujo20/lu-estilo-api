from datetime import date

from pydantic import BaseModel

from app.models import OrderStatus, ProductSection


class FilterPage(BaseModel):
    offset: int = 0
    limit: int = 10


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


class ProductSchema(BaseModel):
    barcode: str
    description: str
    price_cents: int
    section: ProductSection
    inventory: int
    expiration_date: date | None = None


class ProductPublic(ProductSchema):
    id: int


class ProductUpdate(BaseModel):
    barcode: str | None = None
    description: str | None = None
    price_cents: int | None = None
    section: ProductSection | None = None
    inventory: int | None = None
    expiration_date: date | None = None


class ProductList(BaseModel):
    products: list[ProductPublic]


class ProductFilter(FilterPage):
    section: ProductSection | None = None
    price_cents: int | None = None
    inventory: int | None = None


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class FilterClient(FilterPage):
    name: str | None = None
    email: str | None = None


class ItemSchema(BaseModel):
    product_id: int
    quantity: int


class OrderSchema(BaseModel):
    client_id: int
    items: list[ItemSchema]
    status: OrderStatus = OrderStatus.PENDING


class OrderPublic(OrderSchema):
    id: int


class OrderList(BaseModel):
    orders: list[OrderPublic]


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
