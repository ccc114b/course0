# Rust Blog 錯誤修改紀錄

## 錯誤 1: 路由匹配失敗 (404)

**問題描述：**
- 登入後訪問首頁返回 404
- 伺服器有回應，但路由無法匹配

**錯誤訊息：**
```
< HTTP/1.1 404 Not Found
```

**原因：**
- 使用 `web::scope("/")` 包覆所有路由可能導致匹配問題

**修正方式：**
- 移除多餘的 `web::scope("/")`，直接將 routes 註冊到 App

```rust
// 修正前
App::new()
    .service(web::scope("/")
        .service(web::resource("/").to(index))
        ...
    )

// 修正後
App::new()
    .service(web::resource("/").to(index))
    ...
```

---

## 錯誤 2: 路由順序問題 (405 Method Not Allowed)

**問題描述：**
- GET /login 返回 405 Method Not Allowed
- POST /login 卻正常運作

**錯誤訊息：**
```
< HTTP/1.1 405 Method Not Allowed
< allow: POST
```

**原因：**
- 在 actix-web 中，使用 `.to()` (GET) 和 `.route(web::post())` 在同一個 resource 上會有衝突
- 兩個 handler 都註冊到同一個路徑

**修正方式：**
- 將 POST 路由分開，使用不同的路徑

```rust
// 修正前
.service(web::resource("/login").to(login_page))
.service(web::resource("/login").route(web::post().to(login)))

// 修正後
.service(web::resource("/login").to(login_page))
.service(web::resource("/login_post").route(web::post().to(login)))
```

並修改 HTML 表單的 action：
```html
<!-- 修正前 -->
<form method="post" action="/login">

<!-- 修正後 -->
<form method="post" action="/login_post">
```

---

## 錯誤 3: Session 未設定

**問題描述：**
- 登入成功後沒有設定 Cookie
- 重新整理頁面後變成未登入狀態

**原因：**
- 缺少 Session Middleware 設定

**修正方式：**
1. 在 Cargo.toml 加入依賴：
```toml
actix-session = { version = "0.11", features = ["cookie-session"] }
```

2. 在 main.rs 中加入 Session Middleware：
```rust
use actix_web::cookie::Key;
use actix_session::{SessionExt, SessionMiddleware};
use actix_session::storage::CookieSessionStore;

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

---

## 錯誤 4: Cookie Key 長度不足

**問題描述：**
- 伺服器啟動時 panic

**錯誤訊息：**
```
thread 'actix-rt|system:0|arbiter:0' panicked at ...
called `Result::unwrap()` on an `Err` value: TooShort(15)
```

**原因：**
- Cookie Key 長度需要至少 32 bytes
- 最佳實踐是 64 bytes (SHA256)

**修正方式：**
```rust
// 修正前 (長度不足)
let key = Key::from("blog-secret-key".as_bytes()); // 15 bytes

// 修正後 (64 bytes)
let key = Key::from("1234567890123456789012345678901234567890123456789012345678901234".as_bytes());
```

---

## 錯誤 5: 編譯錯誤 - Session 方法未找到

**問題描述：**
- `req.session()` 方法不存在

**錯誤訊息：**
```
error[E0599]: no method named `session` found for struct `HttpRequest`
```

**原因：**
- 未引入 `SessionExt` trait

**修正方式：**
```rust
use actix_session::SessionExt;
```

之後可使用 `req.get_session()` 方法。

---

## 錯誤 6: 編譯錯誤 - Method 類型問題

**問題描述：**
- `web::method::Method::POST` 無法解析

**錯誤訊息：**
```
error[E0433]: failed to resolve: expected type, found function `method`
```

**原因：**
- `web::method` 是函數而非模組

**修正方式：**
```rust
// 修正前
.service(web::resource("/login").route(web::method::Method::POST).to(login))

// 修正後
.service(web::resource("/login").route(web::post().to(login)))
```

---

## 錯誤 7: 編譯錯誤 - 未使用的變數

**問題描述：**
- 編譯出現 unused variable 警告

**錯誤訊息：**
```
warning: unused variable: `user_id`
```

**修正方式：**
在變數前加底線：
```rust
let _user_id: Option<i64> = session.get("userId").ok().flatten();
```

---

## 錯誤 8: 編譯錯誤 - 字串複製問題

**問題描述：**
- `user.username` 在 println 後已被移動

**錯誤訊息：**
```
error[E0382]: borrow of moved value: `user.username`
```

**修正方式：**
```rust
// 修正前
session.insert("username", user.username).ok();
println!("... {}", user.username); // 錯誤：username 已被移動

// 修正後
let username = user.username.clone();
session.insert("username", user.username).ok();
println!("... {}", username);
```

---

## 錯誤 9: 移除了不需要的 imports

**問題描述：**
- 編譯出現 unused imports 警告

**修正方式：**
移除不需要的 import：
```rust
// 移除
use actix_web::http::Method;
use actix_web::dev::ServiceRequest;
```

---

## 錯誤 10: Port 被佔用

**問題描述：**
- 執行 `cargo run` 時出現 Address already in use 錯誤

**錯誤訊息：**
```
Error: Os { code: 48, kind: AddrInUse, message: "Address already in use" }
```

**修正方式：**
建立 `run.sh` 腳本自動殺掉舊程序：
```bash
#!/bin/bash
pkill -f rustblog 2>/dev/null || true
sleep 1
cargo run
```

---

## 總結

| 錯誤類型 | 數量 | 說明 |
|---------|------|------|
| 路由問題 | 2 | 需注意 actix-web 路由註冊方式 |
| Session 問題 | 2 | 需正確設定 Middleware |
| 編譯錯誤 | 5 | 多為 import 與類型問題 |
| 執行環境 | 1 | Port 佔用問題 |

---

## 開發建議

1. **路由註冊**：
   - GET 和 POST 分開註冊
   - 避免在同一 resource 上混用 `.to()` 和 `.route()`

2. **Session**：
   - 使用 actix-session 0.11 版本
   - Key 長度至少 32 bytes

3. **除錯**：
   - 加入 `println!` 追蹤程式執行流程
   - 使用 `curl -v` 查看 HTTP 狀態碼與 headers
