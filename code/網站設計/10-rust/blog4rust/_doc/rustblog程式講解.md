# Rust Blog 程式講解

## 1. 專案架構

```
rustblog/
├── Cargo.toml          # 專案依賴配置
├── run.sh              # 啟動腳本
├── rustblog.db         # SQLite 資料庫 (執行時自動建立)
└── src/
    └── main.rs         # 主程式碼 (約 1000 行)
```

## 2. 主要依賴

```toml
actix-web = "4"        # Web 框架
actix-session = "0.11" # Session 管理
rusqlite = "0.31"      # SQLite 資料庫
bcrypt = "0.15"        # 密碼雜湊
serde = "1.0"          # 序列化/反序列化
```

## 3. 程式碼結構分析

### 3.1 引入模組 (行 1-7)

```rust
use actix_web::{web, App, HttpServer, HttpRequest, HttpResponse, cookie::Key};
use actix_session::{SessionExt, SessionMiddleware};
use actix_session::storage::CookieSessionStore;
use rusqlite::{Connection, params};
use bcrypt::{hash, verify, DEFAULT_COST};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
```

- `actix_web`: Web 框架核心元件
- `actix_session`: Session 中間件，用於管理使用者登入狀態
- `rusqlite`: SQLite 資料庫操作
- `bcrypt`: 密碼加密（不可逆雜湊）
- `serde`: 用於 JSON 序列化

### 3.2 應用程式狀態 (行 8-10)

```rust
struct AppState {
    db: Mutex<Connection>,
}
```

- 使用 `Mutex` 確保執行緒安全
- 所有 HTTP handler 透過 `web::Data<AppState>` 共享資料庫連線

### 3.3 資料庫初始化 (行 12-70)

```rust
fn init_db(conn: &Connection) {
    conn.execute("CREATE TABLE IF NOT EXISTS users (...))", []);
    conn.execute("CREATE TABLE IF NOT EXISTS posts (...))", []);
    conn.execute("CREATE TABLE IF NOT EXISTS comments (...))", []);
    conn.execute("CREATE TABLE IF NOT EXISTS likes (...))", []);
    conn.execute("CREATE TABLE IF NOT EXISTS shares (...))", []);
}
```

建立 5 個資料表：
- **users**: id, username, password, created_at
- **posts**: id, title, content, author_id, created_at
- **comments**: id, post_id, author_id, content, created_at
- **likes**: id, post_id, user_id, created_at (unique: post_id + user_id)
- **shares**: id, post_id, user_id, created_at (unique: post_id + user_id)

### 3.4 資料結構 (行 72-100)

```rust
struct User { id, username, password, created_at }
struct Post { id, title, content, author_id, created_at, username, comment_count, like_count, ... }
struct Comment { id, post_id, author_id, content, created_at, username }
```

使用 `serde` 的 `Serialize`/`Deserialize` 自動轉換 JSON。

### 3.5 HTML 模板 (行 102-180)

```rust
fn layout(title: &str, content: &str) -> String { ... }
fn sidebar(username: Option<&str>, current_page: &str) -> String { ... }
fn format_time(dt: &str) -> String { ... }
```

- `layout()`: 產生完整 HTML 頁面，包含 CSS 樣式
- `sidebar()`: 根據登入狀態產生側邊欄
- `format_time()`: 格式化時間顯示

CSS 樣式採用深色模式 (Twitter/X 風格)。

## 4. HTTP Handler 詳解

### 4.1 首頁 (index) - 行 200-280

```rust
async fn index(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    // 1. 檢查 session
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    // 2. 未登入則轉址到登入頁
    if user_id.is_none() {
        return HttpResponse::Found().append_header(("Location", "/login")).body("");
    }
    
    // 3. 查詢所有文章 (含 username, 按讚/分享數)
    let mut stmt = db.prepare("SELECT posts.*, users.username ...");
    
    // 4. 逐一取得統計數據
    for post in &mut posts {
        let stats = db.query_row(
            "SELECT COUNT(*) FROM comments WHERE post_id = ? ..."
        );
        // 檢查使用者是否按讚/轉分享
        post.user_liked = db.query_row("SELECT id FROM likes ...");
    }
    
    // 5. 產生 HTML 並回傳
    HttpResponse::Ok().body(layout("youbook", &content))
}
```

### 4.2 登入頁面 (login_page) - 行 540-560

```rust
async fn login_page(req: HttpRequest) -> HttpResponse {
    // 已登入則轉址回首頁
    let session = req.get_session();
    if session.get::<i64>("userId").ok().flatten().is_some() {
        return HttpResponse::Found().append_header(("Location", "/")).body("");
    }
    // 回傳登入表單 HTML
}
```

### 4.3 處理登入 (login) - 行 570-600

```rust
async fn login(req: HttpRequest, data: web::Data<AppState>, form: web::Form<LoginForm>) -> HttpResponse {
    // 1. 從資料庫查詢使用者
    let user: User = match db.query_row("SELECT * FROM users WHERE username = ?", ...) {
        Ok(u) => u,
        Err(_) => return HttpResponse::Unauthorized().body("Invalid credentials"),
    };
    
    // 2. 驗證密碼 (bcrypt)
    let valid = verify(&form.password, &user.password).unwrap_or(false);
    if !valid { return HttpResponse::Unauthorized().body("Invalid credentials"); }
    
    // 3. 設定 session
    let session = req.get_session();
    session.insert("userId", user.id).ok();
    session.insert("username", user.username).ok();
    
    // 4. 轉址回首頁
    HttpResponse::Found().append_header(("Location", "/")).body("")
}
```

### 4.4 處理註冊 (register) - 行 630-670

```rust
async fn register(_req: HttpRequest, data: web::Data<AppState>, form: web::Form<LoginForm>) -> HttpResponse {
    // 1. 密碼雜湊 (bcrypt)
    let hash = hash(&form.password, DEFAULT_COST).unwrap();
    
    // 2. 寫入資料庫
    let result = db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        params![&form.username, hash]
    );
    
    // 3. 處理錯誤 (username 重複)
    match result {
        Ok(_) => HttpResponse::Found().append_header(("Location", "/login")).body(""),
        Err(e) if e.to_string().contains("UNIQUE") => 
            HttpResponse::BadRequest().body("Username exists"),
        Err(_) => HttpResponse::InternalServerError().body("Error"),
    }
}
```

### 4.5 發布文章 (create_post) - 行 710-740

```rust
async fn create_post(req: HttpRequest, data: web::Data<AppState>, form: web::Form<PostForm>) -> HttpResponse {
    // 1. 檢查登入
    let session = req.get_session();
    let user_id = session.get::<i64>("userId").ok().flatten();
    
    // 2. 標題取內文前 50 字
    let title = if content.len() > 50 { &content[..50] } else { content };
    
    // 3. 寫入資料庫
    db.execute(
        "INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
        params![title, &form.content, user_id]
    );
    
    // 4. 轉址到 my 頁面
    HttpResponse::Found().append_header(("Location", "/my")).body("")
}
```

### 4.6 按讚功能 (toggle_like) - 行 780-810

```rust
async fn toggle_like(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    // 1. 檢查是否已按讚
    let liked = db.query_row(
        "SELECT id FROM likes WHERE post_id = ? AND user_id = ?",
        params![post_id, user_id],
        |_| Ok(true)
    ).is_ok();
    
    // 2. 切換狀態 (已按讚則刪除，未按則新增)
    if liked {
        db.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", ...);
    } else {
        db.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", ...);
    }
    
    // 3. 回傳 JSON
    HttpResponse::Ok().json(serde_json::json!({"success": true, "liked": !liked}))
}
```

## 5. Session 中間件設定 (行 990-1010)

```rust
HttpServer::new(move || {
    let key = Key::from("64字元的密鑰".as_bytes());
    
    App::new()
        .app_data(state.clone())
        .wrap(
            SessionMiddleware::builder(
                CookieSessionStore::default(),
                key
            )
            .build()
        )
        // ... routes
})
```

- 使用 Cookie 儲存 session
- Key 長度需 64 bytes (SHA256)
- `HttpOnly` 防止 JavaScript 讀取
- `Secure` 僅在 HTTPS 傳輸 (開發環境可關閉)

## 6. 路由設定 (行 1002-1015)

```rust
.service(web::resource("/").to(index))                    // GET 首頁
.service(web::resource("/my").to(my_posts))               // GET 我的文章
.service(web::resource("/user/{id}").to(user_posts))      // GET 用戶文章
.service(web::resource("/post/{id}").to(view_post))       // GET 文章詳情
.service(web::resource("/posts").to(create_post))           // POST 發布文章
.service(web::resource("/post/{id}").route(web::delete().to(delete_post)))
.service(web::resource("/post/{id}/comment").to(add_comment))
.service(web::resource("/post/{id}/like").to(toggle_like))
.service(web::resource("/post/{id}/share").to(toggle_share))
.service(web::resource("/login").to(login_page))            // GET 登入頁
.service(web::resource("/login_post").route(web::post().to(login)))
.service(web::resource("/register").to(register_page))      // GET 註冊頁
.service(web::resource("/register_post").route(web::post().to(register)))
.service(web::resource("/logout").to(logout))
```

## 7. 安全性考量

1. **密碼儲存**: 使用 bcrypt 雜湊，不可逆
2. **Session 安全**: HttpOnly Cookie，防止 XSS
3. **SQL 注入**: 使用 `params![]` 參數化查詢
4. **權限檢查**: 刪除文章、發布評論前檢查 session 中的 userId

## 8. 與 Node.js 版本對照

| Node.js (Express) | Rust (Actix-web) |
|-------------------|------------------|
| `express` | `actix-web` |
| `express-session` | `actix-session` |
| `sqlite3` | `rusqlite` |
| `bcryptjs` | `bcrypt` |
| `app.get()` | `.service(web::resource().to())` |
| `app.post()` | `.route(web::post().to())` |
| `res.send()` | `HttpResponse::Ok().body()` |
| `res.redirect()` | `HttpResponse::Found().append_header(("Location", ...))` |
| `req.session` | `req.get_session()` |
| `req.body` | `web::Form<T>` |

## 9. 執行流程圖

```
使用者瀏覽器
     │
     ▼
HttpServer (port 3000)
     │
     ▼
SessionMiddleware (檢查 Cookie)
     │
     ▼
Router (匹配 URL)
     │
     ▼
Handler 函數
     │
     ├── 讀取 Session ──► AppState::db
     │                        │
     │                        ▼
     │                   SQLite
     │                        │
     ◄───────────────────────┘
     │
     ▼
產生 HTML / JSON
     │
     ▼
Response (含 Set-Cookie header)
```
