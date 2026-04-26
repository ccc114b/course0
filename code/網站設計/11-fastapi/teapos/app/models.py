from sqlmodel import SQLModel, Field
import json
from datetime import datetime
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


class MenuItem(SQLModel, table=True):
    __tablename__ = "menu_items"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(index=True)
    category: str
    price: float
    is_available: bool = True


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    order_number: str = Field(index=True)
    items_json: str = Field(default="[]")
    total_amount: float = 0.0
    discount: float = 0.0
    final_amount: float = 0.0
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @property
    def items(self) -> list[dict]:
        return json.loads(self.items_json)

    @items.setter
    def items(self, value: list[dict]) -> None:
        self.items_json = json.dumps(value)