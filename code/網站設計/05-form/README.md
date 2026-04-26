# Youbook

一個使用 Node.js 和 SQLite 開發的簡單社群部落格系統。

## 功能

- **用戶系統**
  - 用戶註冊與登入
  - 密碼使用 bcrypt 加密
  - Session 管理

- **貼文系統**
  - 發布貼文
  - 查看所有貼文（公開）
  - 查看自己的貼文
  - 查看特定用戶的貼文
  - 刪除自己的貼文

- **互動功能**
  - 喜歡貼文
  - 轉貼貼文
  - 回應貼文

## 技術堆疊

- Node.js + Express
- SQLite (sqlite3)
- bcryptjs（密碼雜湊）
- express-session（Session 管理）

## 安裝與執行

```bash
cd blog
npm install
npm start
```

然後打開 http://localhost:3000

## 專案結構

```
blog/
├── package.json
├── server.js      - Express 伺服器
├── database.js    - SQLite 資料庫初始化
└── blog.db        - SQLite 資料庫檔案
```

## 路由

| 路由 | 說明 |
|------|------|
| `/` | 公開貼文牆（需登入） |
| `/my` | 我的貼文 |
| `/login` | 登入頁面 |
| `/register` | 註冊頁面 |
| `/user/:id` | 用戶的貼文 |
| `/post/:id` | 單篇貼文（含回應） |
| `/logout` | 登出 |