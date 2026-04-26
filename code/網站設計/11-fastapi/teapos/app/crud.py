from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import func
from app.models import MenuItem, Order
from app.schemas import (
    MenuItemCreate,
    MenuItemUpdate,
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    SIZE_PRICE,
    TOPPING_PRICE,
    DiscountCode,
)
from datetime import datetime, date
import json


async def get_menu_items(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[MenuItem]:
    result = await db.execute(select(MenuItem).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_menu_item(db: AsyncSession, item_id: str) -> MenuItem | None:
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    return result.scalar_one_or_none()


async def create_menu_item(db: AsyncSession, payload: MenuItemCreate) -> MenuItem:
    item = MenuItem(**payload.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_menu_item(db: AsyncSession, item_id: str, payload: MenuItemUpdate) -> MenuItem | None:
    item = await get_menu_item(db, item_id)
    if not item:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_menu_item(db: AsyncSession, item_id: str) -> bool:
    item = await get_menu_item(db, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.flush()
    return True


async def get_all_orders(db: AsyncSession, status: str | None = None) -> list[Order]:
    query = select(Order).order_by(Order.created_at.desc())
    if status:
        query = query.where(Order.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: str) -> Order | None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_order_by_number(db: AsyncSession, order_number: str) -> Order | None:
    result = await db.execute(select(Order).where(Order.order_number == order_number))
    return result.scalar_one_or_none()


async def get_next_order_number(db: AsyncSession) -> str:
    today = date.today().strftime("%Y%m%d")
    result = await db.execute(
        select(func.max(Order.order_number)).where(Order.order_number.like(f"{today}%"))
    )
    last_number = result.scalar_one_or_none()
    if last_number:
        counter = int(last_number.split("-")[1]) + 1
        return f"{today}-{counter:03d}"
    return f"{today}-001"


async def calculate_item_price(
    db: AsyncSession, item: OrderItemCreate
) -> tuple[float, str]:
    menu_item = await get_menu_item(db, item.menu_item_id)
    if not menu_item:
        raise ValueError(f"Menu item {item.menu_item_id} not found")

    size_price = SIZE_PRICE.get(item.size.value, 0)
    topping_price = sum(TOPPING_PRICE.get(t, 0) for t in item.toppings)
    unit_price = menu_item.price + size_price + topping_price
    subtotal = unit_price * item.quantity

    return unit_price, menu_item.name


async def create_order(db: AsyncSession, payload: OrderCreate) -> Order:
    order_items: list[OrderItemResponse] = []
    total_amount = 0.0

    for item in payload.items:
        unit_price, name = await calculate_item_price(db, item)
        subtotal = unit_price * item.quantity
        total_amount += subtotal

        order_items.append(
            OrderItemResponse(
                menu_item_id=item.menu_item_id,
                name=name,
                size=item.size.value,
                sweetness=item.sweetness.value,
                ice_level=item.ice_level.value,
                toppings=item.toppings,
                quantity=item.quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
        )

    discount = 0.0
    if payload.discount_code:
        discount = calculate_discount(payload.discount_code, total_amount)

    final_amount = total_amount - discount
    order_number = await get_next_order_number(db)

    order = Order(
        order_number=order_number,
        items_json=json.dumps([item.model_dump() for item in order_items]),
        total_amount=total_amount,
        discount=discount,
        final_amount=final_amount,
        status="pending",
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def update_order_status(db: AsyncSession, order_id: str, status: str) -> Order | None:
    order = await get_order(db, order_id)
    if not order:
        return None
    order.status = status
    order.updated_at = datetime.now().isoformat()
    await db.flush()
    await db.refresh(order)
    return order


async def delete_order(db: AsyncSession, order_id: str) -> bool:
    order = await get_order(db, order_id)
    if not order:
        return False
    await db.delete(order)
    await db.flush()
    return True


def calculate_discount(code: str, amount: float) -> float:
    discount_map = {
        DiscountCode.SAVE10.value: ("percentage", 10),
        DiscountCode.SAVE20.value: ("percentage", 20),
        DiscountCode.FIRST_ORDER.value: ("fixed", 20),
    }

    if code in discount_map:
        discount_type, discount_value = discount_map[code]
        if discount_type == "percentage":
            return round(amount * discount_value / 100, 2)
        else:
            return discount_value
    return 0.0


def validate_discount_code(code: str, order_amount: float) -> dict:
    if code == DiscountCode.SAVE10.value:
        discount = round(order_amount * 10 / 100, 2)
        return {
            "valid": True,
            "discount_type": "percentage",
            "discount_value": 10,
            "final_amount": order_amount - discount,
            "message": "10% discount applied",
        }
    elif code == DiscountCode.SAVE20.value:
        discount = round(order_amount * 20 / 100, 2)
        return {
            "valid": True,
            "discount_type": "percentage",
            "discount_value": 20,
            "final_amount": order_amount - discount,
            "message": "20% discount applied",
        }
    elif code == DiscountCode.FIRST_ORDER.value:
        discount = 20.0
        return {
            "valid": True,
            "discount_type": "fixed",
            "discount_value": 20,
            "final_amount": max(0, order_amount - discount),
            "message": "$20 discount applied",
        }
    return {
        "valid": False,
        "discount_type": None,
        "discount_value": None,
        "final_amount": None,
        "message": "Invalid discount code",
    }


async def get_daily_report(db: AsyncSession, target_date: date | None = None) -> dict:
    if target_date is None:
        target_date = date.today()

    date_str = target_date.strftime("%Y-%m-%d")

    result = await db.execute(
        select(Order).where(Order.created_at.like(f"{date_str}%"))
    )
    orders = list(result.scalars().all())

    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.status == "completed")
    cancelled_orders = sum(1 for o in orders if o.status == "cancelled")
    total_revenue = sum(o.final_amount for o in orders if o.status == "completed")

    drink_counts: dict[str, int] = {}
    for order in orders:
        items = json.loads(order.items_json)
        for item in items:
            drink_name = item.get("name", "Unknown")
            drink_counts[drink_name] = drink_counts.get(drink_name, 0) + item.get("quantity", 0)

    top_drinks = sorted(drink_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_drinks = [{"name": name, "quantity": qty} for name, qty in top_drinks]

    return {
        "date": date_str,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "total_revenue": round(total_revenue, 2),
        "top_drinks": top_drinks,
    }