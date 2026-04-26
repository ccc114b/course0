from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.schemas import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderItemResponse,
    DiscountValidationRequest,
    DiscountValidationResponse,
)
from app import crud

router = APIRouter(prefix="/api/orders", tags=["orders"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[OrderResponse])
async def get_orders(db: DbDep, status: str | None = Query(default=None)) -> list[OrderResponse]:
    orders = await crud.get_all_orders(db, status)
    return [
        OrderResponse(
            id=o.id,
            order_number=o.order_number,
            items=[OrderItemResponse(**item) for item in o.items],
            total_amount=o.total_amount,
            discount=o.discount,
            final_amount=o.final_amount,
            status=o.status,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: DbDep) -> OrderResponse:
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        items=[OrderItemResponse(**item) for item in order.items],
        total_amount=order.total_amount,
        discount=order.discount,
        final_amount=order.final_amount,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, db: DbDep) -> OrderResponse:
    try:
        order = await crud.create_order(db, payload)
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            items=[OrderItemResponse(**item) for item in order.items],
            total_amount=order.total_amount,
            discount=order.discount,
            final_amount=order.final_amount,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(order_id: str, payload: OrderStatusUpdate, db: DbDep) -> OrderResponse:
    order = await crud.update_order_status(db, order_id, payload.status.value)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        items=[OrderItemResponse(**item) for item in order.items],
        total_amount=order.total_amount,
        discount=order.discount,
        final_amount=order.final_amount,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str, db: DbDep) -> None:
    deleted = await crud.delete_order(db, order_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.post("/validate-discount", response_model=DiscountValidationResponse)
async def validate_discount(payload: DiscountValidationRequest) -> DiscountValidationResponse:
    result = crud.validate_discount_code(payload.code, payload.order_amount)
    return DiscountValidationResponse(**result)