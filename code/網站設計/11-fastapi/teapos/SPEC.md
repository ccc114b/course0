# Bubble Tea POS System - Specification

## 1. Project Overview
- **Project Name**: Bubble Tea POS System
- **Type**: RESTful API Backend
- **Core Functionality**: Order management, menu handling, and daily reporting for a bubble tea shop
- **Target Users**: Store staff and managers

## 2. Tech Stack
- **Framework**: FastAPI with Pydantic V2
- **Database**: SQLite with SQLAlchemy async
- **API Documentation**: Auto-generated Swagger UI at `/docs`

## 3. Data Models

### MenuItem
- `id`: UUID (primary key)
- `name`: str (drink name)
- `category`: str (tea, milk tea, specialty)
- `price`: float (base price)
- `is_available`: bool

### Order
- `id`: UUID (primary key)
- `order_number`: str (format: YYYYMMDD-XXX)
- `items`: JSON (list of order items)
- `total_amount`: float
- `discount`: float
- `final_amount`: float
- `status`: enum (pending, preparing, ready, completed, cancelled)
- `created_at`: datetime
- `updated_at`: datetime

### OrderItem (embedded in Order.items)
- `menu_item_id`: UUID
- `name`: str
- `size`: str (S/M/L)
- `sweetness`: str (no sugar, light, half, less, normal)
- `ice_level`: str (no ice, light, less, normal)
- `toppings`: list[str]
- `quantity`: int
- `unit_price`: float
- `subtotal`: float

## 4. API Endpoints

### Menu
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/menu` | Get all menu items |
| GET | `/api/menu/{item_id}` | Get specific menu item |
| POST | `/api/menu` | Create menu item |
| PUT | `/api/menu/{item_id}` | Update menu item |
| DELETE | `/api/menu/{item_id}` | Delete menu item |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orders` | Get all orders (filter by status) |
| GET | `/api/orders/{order_id}` | Get specific order |
| POST | `/api/orders` | Create new order |
| PUT | `/api/orders/{order_id}/status` | Update order status |
| DELETE | `/api/orders/{order_id}` | Cancel order |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/daily` | Get daily sales report |

### Discounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders/validate-discount` | Validate discount code |

## 5. Pricing Rules

### Drink Sizes (price addition)
- S: +0
- M: +5
- L: +10

### Toppings (price per addition)
- Pearl (珍珠): 5
- Boba (波霸): 5
- Coconut Jelly (椰果): 5
- Taro Ball (芋圓): 8
- Pudding (布丁): 10

### Sweetness Levels
- No Sugar (無糖)
- Light (微糖)
- Half (半糖)
- Less (少糖)
- Normal (正常)

### Ice Levels
- No Ice (去冰)
- Light (微冰)
- Less (少冰)
- Normal (正常)

## 6. Default Menu Data
| Name | Category | Price |
|------|----------|-------|
| Pearl Milk Tea (珍珠奶茶) | Milk Tea | 55 |
| Boba Milk Tea (波霸奶茶) | Milk Tea | 60 |
| Coconut Jelly Milk Tea (椰果奶茶) | Milk Tea | 55 |
| Oolong Milk Tea (烏龍奶茶) | Milk Tea | 55 |
| Black Tea (紅茶) | Tea | 35 |
| Green Tea (綠茶) | Tea | 35 |
| Matcha Latte (抹茶拿鐵) | Specialty | 70 |
| Taro Milk (芋頭牛奶) | Specialty | 65 |

## 7. Order Status Flow
```
pending -> preparing -> ready -> completed
    |                      |
    +-----> cancelled <----+
```

## 8. Constraints
- Use type hints everywhere
- Use Pydantic V2 syntax
- Use `Annotated` pattern for dependency injection
- Use async/await for all I/O operations
- Return proper HTTP status codes
- All prices in TWD (New Taiwan Dollar)