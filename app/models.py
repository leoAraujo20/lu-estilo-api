from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()


class ProductSection(Enum):
    CLOTHING = 'clothing'
    SHOES = 'shoes'
    ACCESSORIES = 'accessories'


class OrderStatus(Enum):
    PENDING = 'pending'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)


@table_registry.mapped_as_dataclass
class Client:
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    cpf: Mapped[str] = mapped_column(nullable=False, unique=True)
    orders: Mapped[list['Order']] = relationship(
        init=False, back_populates='client', lazy='selectin'
    )


@table_registry.mapped_as_dataclass
class Product:
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    barcode: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False)
    price_cents: Mapped[int] = mapped_column(nullable=False)
    section: Mapped[ProductSection] = mapped_column(nullable=False)
    inventory: Mapped[int] = mapped_column(nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(
        nullable=True, default=None
    )
    items: Mapped[list['Item']] = relationship(
        init=False, back_populates='product', lazy='selectin'
    )


@table_registry.mapped_as_dataclass
class Order:
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'))
    client: Mapped['Client'] = relationship(
        back_populates='orders', init=False
    )
    items: Mapped[list['Item']] = relationship(
        cascade='all, delete-orphan',
        back_populates='order',
        lazy='selectin',
        init=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        default=OrderStatus.PENDING, nullable=False
    )
    order_date: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc), nullable=False
    )


@table_registry.mapped_as_dataclass
class Item:
    __tablename__ = 'items'
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order: Mapped['Order'] = relationship(
        back_populates='items',
        init=False,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    product: Mapped['Product'] = relationship(
        back_populates='items',
        init=False,
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id'), default=None, nullable=False
    )
