from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.schemas import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from app import crud

router = APIRouter(prefix="/api/menu", tags=["menu"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[MenuItemResponse])
async def get_menu(db: DbDep, skip: int = 0, limit: int = 100) -> list[MenuItemResponse]:
    items = await crud.get_menu_items(db, skip, limit)
    return items


@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(item_id: str, db: DbDep) -> MenuItemResponse:
    item = await crud.get_menu_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return item


@router.post("", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(payload: MenuItemCreate, db: DbDep) -> MenuItemResponse:
    return await crud.create_menu_item(db, payload)


@router.put("/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(item_id: str, payload: MenuItemUpdate, db: DbDep) -> MenuItemResponse:
    item = await crud.update_menu_item(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(item_id: str, db: DbDep) -> None:
    deleted = await crud.delete_menu_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")