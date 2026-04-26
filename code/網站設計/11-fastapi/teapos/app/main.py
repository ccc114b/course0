from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.database import init_db, async_session
from app.routers import menu, orders, reports
from app.schemas import MenuItemCreate


DEFAULT_MENU_ITEMS = [
    {"name": "珍珠奶茶", "category": "Milk Tea", "price": 55.0},
    {"name": "波霸奶茶", "category": "Milk Tea", "price": 60.0},
    {"name": "椰果奶茶", "category": "Milk Tea", "price": 55.0},
    {"name": "烏龍奶茶", "category": "Milk Tea", "price": 55.0},
    {"name": "紅茶", "category": "Tea", "price": 35.0},
    {"name": "綠茶", "category": "Tea", "price": 35.0},
    {"name": "抹茶拿鐵", "category": "Specialty", "price": 70.0},
    {"name": "芋頭牛奶", "category": "Specialty", "price": 65.0},
]


async def seed_default_menu() -> None:
    from sqlalchemy import select
    from app.models import MenuItem

    async with async_session() as session:
        result = await session.execute(select(MenuItem))
        existing_items = result.scalars().all()

        if len(existing_items) == 0:
            for item_data in DEFAULT_MENU_ITEMS:
                item = MenuItem(**item_data)
                session.add(item)
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_default_menu()
    yield


app = FastAPI(
    title="Bubble Tea POS System",
    description="珍珠奶茶店 POS 系統 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    return FileResponse("app/frontend.html", media_type="text/html")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}