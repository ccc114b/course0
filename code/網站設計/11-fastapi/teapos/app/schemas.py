from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Annotated
from enum import Enum


class DrinkSize(str, Enum):
    S = "S"
    M = "M"
    L = "L"


class SweetnessLevel(str, Enum):
    NO_SUGAR = "no_sugar"
    LIGHT = "light"
    HALF = "half"
    LESS = "less"
    NORMAL = "normal"


class IceLevel(str, Enum):
    NO_ICE = "no_ice"
    LIGHT = "light"
    LESS = "less"
    NORMAL = "normal"


SIZE_PRICE = {"S": 0, "M": 5, "L": 10}
TOPPING_PRICE = {
    "pearl": 5,
    "boba": 5,
    "coconut_jelly": 5,
    "taro_ball": 8,
    "pudding": 10,
}


class MenuItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    is_available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    price: float | None = Field(default=None, gt=0)
    is_available: bool | None = None


class MenuItemResponse(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class OrderItemCreate(BaseModel):
    menu_item_id: str
    size: DrinkSize = DrinkSize.M
    sweetness: SweetnessLevel = SweetnessLevel.HALF
    ice_level: IceLevel = IceLevel.NORMAL
    toppings: list[str] = Field(default_factory=list)
    quantity: int = Field(gt=0, le=100)

    @field_validator("toppings", mode="before")
    @classmethod
    def validate_toppings(cls, v: list[str]) -> list[str]:
        valid_toppings = set(TOPPING_PRICE.keys())
        for topping in v:
            if topping not in valid_toppings:
                raise ValueError(f"Invalid topping: {topping}")
        return v


class OrderItemResponse(BaseModel):
    menu_item_id: str
    name: str
    size: str
    sweetness: str
    ice_level: str
    toppings: list[str]
    quantity: int
    unit_price: float
    subtotal: float


class OrderStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    discount_code: str | None = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_number: str
    items: list[OrderItemResponse]
    total_amount: float
    discount: float
    final_amount: float
    status: str
    created_at: str
    updated_at: str


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class DailyReport(BaseModel):
    date: str
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: float
    top_drinks: list[dict[str, int | str]]


class DiscountCode(str, Enum):
    SAVE10 = "SAVE10"
    SAVE20 = "SAVE20"
    FIRST_ORDER = "FIRST_ORDER"


class DiscountValidationRequest(BaseModel):
    code: str
    order_amount: float


class DiscountValidationResponse(BaseModel):
    valid: bool
    discount_type: str | None = None
    discount_value: float | None = None
    final_amount: float | None = None
    message: str