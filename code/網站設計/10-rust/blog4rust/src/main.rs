use actix_web::{web, App, HttpServer, HttpRequest, HttpResponse, cookie::Key};
use actix_session::{SessionExt, SessionMiddleware};
use actix_session::storage::CookieSessionStore;
use rusqlite::{Connection, params};
use bcrypt::{hash, verify, DEFAULT_COST};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;

struct AppState {
    db: Mutex<Connection>,
}

fn init_db(conn: &Connection) {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )",
        [],
    ).unwrap();
    
    conn.execute(
        "CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )",
        [],
    ).unwrap();
    
    conn.execute(
        "CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (author_id) REFERENCES users(id)
        )",
        [],
    ).unwrap();
    
    conn.execute(
        "CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(post_id, user_id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )",
        [],
    ).unwrap();
    
    conn.execute(
        "CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(post_id, user_id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )",
        [],
    ).unwrap();
}

#[derive(Debug, Serialize, Deserialize)]
struct User {
    id: i64,
    username: String,
    password: String,
    created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct Post {
    id: i64,
    title: String,
    content: String,
    author_id: i64,
    created_at: String,
    username: Option<String>,
    comment_count: i64,
    like_count: i64,
    share_count: i64,
    user_liked: bool,
    user_shared: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct Comment {
    id: i64,
    post_id: i64,
    author_id: i64,
    content: String,
    created_at: String,
    username: Option<String>,
}

fn layout(title: &str, content: &str) -> String {
    format!(r#"<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #000; color: #fff; min-height: 100vh; }}
    .container {{ display: flex; min-height: 100vh; }}
    .sidebar {{ width: 280px; padding: 20px; border-right: 1px solid #2d2d2d; position: fixed; height: 100vh; }}
    .main {{ margin-left: 280px; flex: 1; max-width: 700px; min-height: 100vh; border-right: 1px solid #2d2d2d; }}
    .logo {{ font-size: 24px; font-weight: bold; padding: 15px 0; margin-bottom: 20px; }}
    .logo a {{ color: #fff; text-decoration: none; }}
    .nav-item {{ padding: 15px; font-size: 18px; border-radius: 30px; margin-bottom: 5px; display: block; color: #fff; text-decoration: none; }}
    .nav-item:hover {{ background: #1a1a1a; }}
    .nav-item.active {{ font-weight: bold; }}
    .user-profile {{ padding: 15px; border-radius: 30px; display: flex; align-items: center; gap: 12px; margin-top: 20px; background: #1a1a1a; }}
    .avatar {{ width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; }}
    .user-info {{ flex: 1; }}
    .user-name {{ font-weight: bold; }}
    .user-handle {{ color: #71767b; font-size: 14px; }}
    .btn {{ padding: 10px 20px; border-radius: 20px; border: none; cursor: pointer; font-size: 14px; font-weight: bold; }}
    .btn-primary {{ background: #fff; color: #000; width: 100%; }}
    .btn-primary:hover {{ background: #e6e6e6; }}
    .header {{ padding: 20px; border-bottom: 1px solid #2d2d2d; position: sticky; top: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); z-index: 100; }}
    .header h1 {{ font-size: 20px; font-weight: bold; }}
    .post-form {{ padding: 20px; border-bottom: 1px solid #2d2d2d; }}
    .post-form textarea {{ width: 100%; background: transparent; border: none; color: #fff; font-size: 18px; resize: none; min-height: 80px; outline: none; }}
    .post-form textarea::placeholder {{ color: #71767b; }}
    .post-form-actions {{ display: flex; justify-content: flex-end; margin-top: 10px; }}
    .post {{ padding: 20px; border-bottom: 1px solid #2d2d2d; transition: background 0.2s; }}
    .post:hover {{ background: #0a0a0a; }}
    .post-link {{ text-decoration: none; color: inherit; display: block; }}
    .post-header {{ display: flex; gap: 12px; margin-bottom: 10px; }}
    .post-avatar {{ width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-weight: bold; }}
    .post-user-info {{ flex: 1; }}
    .post-name {{ font-weight: bold; }}
    .post-name a {{ color: #fff; text-decoration: none; }}
    .post-name a:hover {{ text-decoration: underline; }}
    .post-handle {{ color: #71767b; }}
    .post-time {{ color: #71767b; }}
    .post-content {{ font-size: 16px; line-height: 1.5; margin-bottom: 12px; white-space: pre-wrap; }}
    .delete-btn {{ color: #f4212e; cursor: pointer; margin-left: auto; }}
    .post-actions {{ display: flex; gap: 20px; margin-top: 12px; }}
    .post-action {{ display: flex; align-items: center; gap: 6px; color: #71767b; cursor: pointer; }}
    .post-action:hover {{ color: #1d9bf0; }}
    .post-action.liked {{ color: #f91880; }}
    .post-action.shared {{ color: #00ba7c; }}
    .post-action span {{ font-size: 14px; }}
    .empty-state {{ text-align: center; padding: 60px 20px; color: #71767b; }}
    input {{ width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #2d2d2d; background: #000; color: #fff; font-size: 16px; }}
    .form-container {{ max-width: 400px; margin: 100px auto; padding: 30px; }}
    .form-title {{ font-size: 28px; font-weight: bold; margin-bottom: 30px; }}
    .auth-links {{ margin-top: 20px; text-align: center; color: #71767b; }}
    .auth-links a {{ color: #1d9bf0; text-decoration: none; }}
    .back-link {{ color: #1d9bf0; text-decoration: none; padding: 20px; display: block; border-bottom: 1px solid #2d2d2d; }}
  </style>
</head>
<body>
  {content}
</body>
</html>"#, title = title, content = content)
}

fn sidebar(username: Option<&str>, current_page: &str) -> String {
    match username {
        Some(name) => {
            let initial = name.chars().next().map(|c| c.to_uppercase().to_string()).unwrap_or_default();
            let active_public = if current_page == "public" { "active" } else { "" };
            let active_my = if current_page == "my" { "active" } else { "" };
            format!(r#"
      <div class="sidebar">
        <div class="logo"><a href="/">youbook</a></div>
        <a href="/" class="nav-item {active_public}">Public</a>
        <a href="/my" class="nav-item {active_my}">My Posts</a>
        
        <div class="user-profile">
          <div class="avatar">{initial}</div>
          <div class="user-info">
            <div class="user-name">{name}</div>
            <div class="user-handle">@{name}</div>
          </div>
        </div>
        <a href="/logout" class="nav-item" style="margin-top: 20px;">Log out</a>
      </div>
    "#)
        }
        None => {
            let active_login = if current_page == "login" { "active" } else { "" };
            let active_register = if current_page == "register" { "active" } else { "" };
            format!(r#"
      <div class="sidebar">
        <div class="logo"><a href="/">youbook</a></div>
        <a href="/login" class="nav-item {active_login}">Login</a>
        <a href="/register" class="nav-item {active_register}">Register</a>
      </div>
    "#)
        }
    }
}

fn format_time(dt: &str) -> String {
    dt.replace("T", " ").replace("+08:00", "")
}

async fn index(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    let username: Option<String> = session.get("username").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Found().append_header(("Location", "/login")).body("");
    }
    
    let db = data.db.lock().unwrap();
    
    let mut stmt = db.prepare(
        "SELECT posts.*, users.username 
         FROM posts LEFT JOIN users ON posts.author_id = users.id 
         ORDER BY posts.created_at DESC"
    ).unwrap();
    
    let posts_iter = stmt.query_map([], |row| {
        Ok(Post {
            id: row.get(0)?,
            title: row.get(1)?,
            content: row.get(2)?,
            author_id: row.get(3)?,
            created_at: row.get(4)?,
            username: row.get(5).ok(),
            comment_count: 0,
            like_count: 0,
            share_count: 0,
            user_liked: false,
            user_shared: false,
        })
    }).unwrap();
    
    let mut posts: Vec<Post> = posts_iter.filter_map(|p| p.ok()).collect();
    
    for post in &mut posts {
        let stats: (i64, i64, i64) = db.query_row(
            "SELECT (SELECT COUNT(*) FROM comments WHERE post_id = ?) as comment_count, 
                    (SELECT COUNT(*) FROM likes WHERE post_id = ?) as like_count, 
                    (SELECT COUNT(*) FROM shares WHERE post_id = ?) as share_count",
            params![post.id, post.id, post.id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?))
        ).unwrap_or((0, 0, 0));
        
        post.comment_count = stats.0;
        post.like_count = stats.1;
        post.share_count = stats.2;
        
        if let Some(uid) = user_id {
            post.user_liked = db.query_row(
                "SELECT id FROM likes WHERE post_id = ? AND user_id = ?",
                params![post.id, uid],
                |_| Ok(true)
            ).is_ok();
            
            post.user_shared = db.query_row(
                "SELECT id FROM shares WHERE post_id = ? AND user_id = ?",
                params![post.id, uid],
                |_| Ok(true)
            ).is_ok();
        }
    }
    
    let posts_html: String = posts.iter().map(|post| {
        let name = post.username.as_deref().unwrap_or("Unknown");
        let initial = name.chars().next().map(|c| c.to_uppercase().to_string()).unwrap_or_default();
        
        format!(r#"
          <a href="/post/{}" class="post-link">
            <div class="post">
              <div class="post-header">
                <div class="post-avatar">{}</div>
                <div class="post-user-info">
                  <span class="post-name"><a href="/user/{}">{}</a></span>
                  <span class="post-handle">@{}</span>
                  <span class="post-time"> · {}</span>
                </div>
              </div>
              <div class="post-content">{}</div>
              <div class="post-actions">
                <div class="post-action {}" onclick="event.preventDefault(); event.stopPropagation(); fetch('/post/{}/like', {{method: 'POST'}}).then(() => location.reload())">
                  <span>{}</span>
                  <span>{}</span>
                </div>
                <div class="post-action" onclick="event.preventDefault(); event.stopPropagation(); window.location.href='/post/{}'">
                  <span>💬</span>
                  <span>{}</span>
                </div>
                <div class="post-action {}" onclick="event.preventDefault(); event.stopPropagation(); fetch('/post/{}/share', {{method: 'POST'}}).then(() => location.reload())">
                  <span>{}</span>
                  <span>{}</span>
                </div>
              </div>
            </div>
          </a>
        "#,
            post.id,
            initial,
            post.author_id,
            name,
            name,
            format_time(&post.created_at),
            post.content,
            if post.user_liked { "liked" } else { "" },
            post.id,
            if post.user_liked { "❤️" } else { "🤍" },
            post.like_count,
            post.id,
            post.comment_count,
            if post.user_shared { "shared" } else { "" },
            post.id,
            if post.user_shared { "🔄" } else { "↗️" },
            post.share_count
        )
    }).collect();
    
    let sidebar_html = sidebar(username.as_deref(), "public");
    let content = format!(r#"
      <div class="container">
        {}
        <div class="main">
          <div class="header">
            <h1>Public Posts</h1>
          </div>
          
          {}
        </div>
      </div>
    "#, sidebar_html, if posts.is_empty() { "<div class=\"empty-state\">No posts yet.</div>".to_string() } else { posts_html });
    
    HttpResponse::Ok().body(layout("youbook", &content))
}

async fn my_posts(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    let username: Option<String> = session.get("username").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Found().append_header(("Location", "/login")).body("");
    }
    
    let user_id = user_id.unwrap();
    let username = username.unwrap();
    let db = data.db.lock().unwrap();
    
    let mut stmt = db.prepare(
        "SELECT posts.*, users.username 
         FROM posts LEFT JOIN users ON posts.author_id = users.id 
         WHERE author_id = ? ORDER BY posts.created_at DESC"
    ).unwrap();
    
    let posts_iter = stmt.query_map(params![user_id], |row| {
        Ok(Post {
            id: row.get(0)?,
            title: row.get(1)?,
            content: row.get(2)?,
            author_id: row.get(3)?,
            created_at: row.get(4)?,
            username: row.get(5).ok(),
            comment_count: 0,
            like_count: 0,
            share_count: 0,
            user_liked: false,
            user_shared: false,
        })
    }).unwrap();
    
    let mut posts: Vec<Post> = posts_iter.filter_map(|p| p.ok()).collect();
    
    for post in &mut posts {
        let count: i64 = db.query_row(
            "SELECT COUNT(*) FROM comments WHERE post_id = ?",
            params![post.id],
            |row| row.get(0)
        ).unwrap_or(0);
        post.comment_count = count;
    }
    
    let posts_html: String = posts.iter().map(|post| {
        let initial = username.chars().next().map(|c: char| c.to_uppercase().to_string()).unwrap_or_default();
        
        format!(r#"
          <a href="/post/{}" class="post-link">
            <div class="post">
              <div class="post-header">
                <div class="post-avatar">{}</div>
                <div class="post-user-info">
                  <span class="post-name">{}</span>
                  <span class="post-handle">@{}</span>
                  <span class="post-time"> · {}</span>
                </div>
                <span class="delete-btn" onclick="event.stopPropagation(); if(confirm('Delete this post?')) fetch('/post/{}', {{method: 'DELETE'}}).then(() => location.reload())">✕</span>
              </div>
              <div class="post-content">{}</div>
            </div>
          </a>
        "#,
            post.id,
            initial,
            username,
            username,
            format_time(&post.created_at),
            post.id,
            post.content
        )
    }).collect();
    
    let sidebar_html = sidebar(Some(&username), "my");
    let content = format!(r#"
      <div class="container">
        {}
        <div class="main">
          <div class="header">
            <h1>My Posts</h1>
          </div>
          
          <div class="post-form">
            <form method="post" action="/posts">
              <textarea name="content" placeholder="What is on your mind?" required></textarea>
              <div class="post-form-actions">
                <button type="submit" class="btn btn-primary">Post</button>
              </div>
            </form>
          </div>
          
          {}
        </div>
      </div>
    "#, sidebar_html, if posts.is_empty() { "<div class=\"empty-state\">No posts yet. Share something!</div>".to_string() } else { posts_html });
    
    HttpResponse::Ok().body(layout("My Posts", &content))
}

async fn user_posts(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let _user_id: Option<i64> = session.get("userId").ok().flatten();
    let path = req.path();
    let id_str = path.strip_prefix("/user/").unwrap_or("");
    let target_id: i64 = id_str.parse().unwrap_or(0);
    
    let db = data.db.lock().unwrap();
    
    let user: User = match db.query_row(
        "SELECT * FROM users WHERE id = ?",
        params![target_id],
        |row| Ok(User {
            id: row.get(0)?,
            username: row.get(1)?,
            password: row.get(2)?,
            created_at: row.get(3)?,
        })
    ) {
        Ok(u) => u,
        Err(_) => return HttpResponse::NotFound().body("User not found"),
    };
    
    let mut stmt = db.prepare(
        "SELECT posts.*, users.username 
         FROM posts LEFT JOIN users ON posts.author_id = users.id 
         WHERE author_id = ? ORDER BY posts.created_at DESC"
    ).unwrap();
    
    let posts_iter = stmt.query_map(params![target_id], |row| {
        Ok(Post {
            id: row.get(0)?,
            title: row.get(1)?,
            content: row.get(2)?,
            author_id: row.get(3)?,
            created_at: row.get(4)?,
            username: row.get(5).ok(),
            comment_count: 0,
            like_count: 0,
            share_count: 0,
            user_liked: false,
            user_shared: false,
        })
    }).unwrap();
    
    let posts: Vec<Post> = posts_iter.filter_map(|p| p.ok()).collect();
    
    let posts_html: String = posts.iter().map(|post| {
        let initial = user.username.chars().next().map(|c| c.to_uppercase().to_string()).unwrap_or_default();
        
        format!(r#"
          <a href="/post/{}" class="post-link">
            <div class="post">
              <div class="post-header">
                <div class="post-avatar">{}</div>
                <div class="post-user-info">
                  <span class="post-name"><a href="/user/{}">{}</a></span>
                  <span class="post-handle">@{}</span>
                  <span class="post-time"> · {}</span>
                </div>
              </div>
              <div class="post-content">{}</div>
              <div class="post-actions">
                <div class="post-action" onclick="event.preventDefault(); event.stopPropagation(); window.location.href='/post/{}'">
                  <span>💬</span>
                  <span>0</span>
                </div>
              </div>
            </div>
          </a>
        "#,
            post.id,
            initial,
            user.id,
            user.username,
            user.username,
            format_time(&post.created_at),
            post.content,
            post.id
        )
    }).collect();
    
    let sidebar_html = sidebar(None, "");
    
    let content = format!(r#"
      <div class="container">
        {}
        <div class="main" style="margin-left: 280px;">
          <a href="/" class="back-link">← Back</a>
          <div class="header">
            <h1>@{username}'s Posts</h1>
          </div>
          
          {posts}
        </div>
      </div>
    "#, sidebar_html, username = user.username, posts = if posts.is_empty() { "<div class=\"empty-state\">No posts yet.</div>".to_string() } else { posts_html });
    
    HttpResponse::Ok().body(layout(&format!("@{}", user.username), &content))
}

async fn view_post(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    let path = req.path();
    let id_str = path.strip_prefix("/post/").unwrap_or("");
    let post_id: i64 = id_str.parse().unwrap_or(0);
    
    let db = data.db.lock().unwrap();
    
    let post: Post = match db.query_row(
        "SELECT posts.*, users.username 
         FROM posts LEFT JOIN users ON posts.author_id = users.id 
         WHERE posts.id = ?",
        params![post_id],
        |row| Ok(Post {
            id: row.get(0)?,
            title: row.get(1)?,
            content: row.get(2)?,
            author_id: row.get(3)?,
            created_at: row.get(4)?,
            username: row.get(5).ok(),
            comment_count: 0,
            like_count: 0,
            share_count: 0,
            user_liked: false,
            user_shared: false,
        })
    ) {
        Ok(p) => p,
        Err(_) => return HttpResponse::NotFound().body("Post not found"),
    };
    
    let mut stmt = db.prepare(
        "SELECT comments.*, users.username 
         FROM comments LEFT JOIN users ON comments.author_id = users.id 
         WHERE post_id = ? ORDER BY comments.created_at DESC"
    ).unwrap();
    
    let comments_iter = stmt.query_map(params![post_id], |row| {
        Ok(Comment {
            id: row.get(0)?,
            post_id: row.get(1)?,
            author_id: row.get(2)?,
            content: row.get(3)?,
            created_at: row.get(4)?,
            username: row.get(5).ok(),
        })
    }).unwrap();
    
    let comments: Vec<Comment> = comments_iter.filter_map(|c| c.ok()).collect();
    
    let comments_html: String = comments.iter().map(|comment| {
        let name = comment.username.as_deref().unwrap_or("?");
        let initial = name.chars().next().map(|c| c.to_uppercase().to_string()).unwrap_or_default();
        
        format!(r#"
          <div class="post">
            <div class="post-header">
              <div class="post-avatar">{}</div>
              <div class="post-user-info">
                <span class="post-name"><a href="/user/{}">{}</a></span>
                <span class="post-handle">@{}</span>
                <span class="post-time"> · {}</span>
              </div>
            </div>
            <div class="post-content">{}</div>
          </div>
        "#,
            initial,
            comment.author_id,
            name,
            name,
            format_time(&comment.created_at),
            comment.content
        )
    }).collect();
    
    let post_name = post.username.as_deref().unwrap_or("Unknown");
    let post_initial = post_name.chars().next().map(|c| c.to_uppercase().to_string()).unwrap_or_default();
    
    let is_logged_in = user_id.is_some();
    let comment_form = if is_logged_in {
        format!(r#"
          <div class="post-form">
            <form method="post" action="/post/{}/comment">
              <textarea name="content" placeholder="Write a reply..." required></textarea>
              <div class="post-form-actions">
                <button type="submit" class="btn btn-primary">Reply</button>
              </div>
            </form>
          </div>
        "#, post_id)
    } else {
        "<div class=\"empty-state\"><a href=\"/login\">Log in</a> to reply to this post.</div>".to_string()
    };
    
    let sidebar_html = sidebar(None, "");
    
    let content = format!(r#"
      <div class="container">
        {}
        <div class="main" style="margin-left: 280px;">
          <a href="/" class="back-link">← Back</a>
          <div class="post">
            <div class="post-header">
              <div class="post-avatar">{}</div>
              <div class="post-user-info">
                <span class="post-name"><a href="/user/{}">{}</a></span>
                <span class="post-handle">@{}</span>
                <span class="post-time"> · {}</span>
              </div>
            </div>
            <div class="post-content" style="font-size: 20px;">{}</div>
          </div>
          {}
          <div class="header">
            <h1>Replies</h1>
          </div>
          {}
        </div>
      </div>
    "#,
        sidebar_html,
        post_initial,
        post.author_id,
        post_name,
        post_name,
        format_time(&post.created_at),
        post.content,
        comment_form,
        if comments.is_empty() { "<div class=\"empty-state\">No replies yet.</div>".to_string() } else { comments_html }
    );
    
    let title = if post.content.len() > 50 { &post.content[..50] } else { &post.content };
    HttpResponse::Ok().body(layout(title, &content))
}

#[derive(Deserialize)]
struct PostForm {
    content: String,
}

async fn create_post(req: HttpRequest, data: web::Data<AppState>, form: web::Form<PostForm>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Found().append_header(("Location", "/login")).body("");
    }
    
    let user_id = user_id.unwrap();
    let content = &form.content;
    
    if content.is_empty() {
        return HttpResponse::BadRequest().body("Content required");
    }
    
    let title = if content.len() > 50 { &content[..50] } else { content.as_str() };
    
    let db = data.db.lock().unwrap();
    db.execute(
        "INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
        params![title, content, user_id]
    ).unwrap();
    
    HttpResponse::Found().append_header(("Location", "/my")).body("")
}

async fn delete_post(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Unauthorized().body("");
    }
    
    let path = req.path();
    let id_str = path.strip_prefix("/post/").unwrap_or("");
    let post_id: i64 = id_str.parse().unwrap_or(0);
    
    let db = data.db.lock().unwrap();
    db.execute(
        "DELETE FROM posts WHERE id = ? AND author_id = ?",
        params![post_id, user_id.unwrap()]
    ).unwrap();
    
    HttpResponse::Ok().json(serde_json::json!({"success": true}))
}

async fn add_comment(req: HttpRequest, data: web::Data<AppState>, form: web::Form<PostForm>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Found().append_header(("Location", "/login")).body("");
    }
    
    let path = req.path();
    let id_str = path.strip_prefix("/post/").unwrap_or("").strip_suffix("/comment").unwrap_or("");
    let post_id: i64 = id_str.parse().unwrap_or(0);
    let content = &form.content;
    
    if content.is_empty() {
        return HttpResponse::BadRequest().body("Content required");
    }
    
    let db = data.db.lock().unwrap();
    db.execute(
        "INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)",
        params![post_id, user_id.unwrap(), content]
    ).unwrap();
    
    HttpResponse::Found().append_header(("Location", format!("/post/{}", post_id))).body("")
}

async fn toggle_like(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Unauthorized().body("");
    }
    
    let path = req.path();
    let id_str = path.strip_prefix("/post/").unwrap_or("").strip_suffix("/like").unwrap_or("");
    let post_id: i64 = id_str.parse().unwrap_or(0);
    
    let db = data.db.lock().unwrap();
    let liked = db.query_row(
        "SELECT id FROM likes WHERE post_id = ? AND user_id = ?",
        params![post_id, user_id.unwrap()],
        |_| Ok(true)
    ).is_ok();
    
    if liked {
        db.execute(
            "DELETE FROM likes WHERE post_id = ? AND user_id = ?",
            params![post_id, user_id.unwrap()]
        ).unwrap();
    } else {
        db.execute(
            "INSERT INTO likes (post_id, user_id) VALUES (?, ?)",
            params![post_id, user_id.unwrap()]
        ).unwrap();
    }
    
    HttpResponse::Ok().json(serde_json::json!({"success": true, "liked": !liked}))
}

async fn toggle_share(req: HttpRequest, data: web::Data<AppState>) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_none() {
        return HttpResponse::Unauthorized().body("");
    }
    
    let path = req.path();
    let id_str = path.strip_prefix("/post/").unwrap_or("").strip_suffix("/share").unwrap_or("");
    let post_id: i64 = id_str.parse().unwrap_or(0);
    
    let db = data.db.lock().unwrap();
    let shared = db.query_row(
        "SELECT id FROM shares WHERE post_id = ? AND user_id = ?",
        params![post_id, user_id.unwrap()],
        |_| Ok(true)
    ).is_ok();
    
    if shared {
        db.execute(
            "DELETE FROM shares WHERE post_id = ? AND user_id = ?",
            params![post_id, user_id.unwrap()]
        ).unwrap();
    } else {
        db.execute(
            "INSERT INTO shares (post_id, user_id) VALUES (?, ?)",
            params![post_id, user_id.unwrap()]
        ).unwrap();
    }
    
    HttpResponse::Ok().json(serde_json::json!({"success": true, "shared": !shared}))
}

async fn login_page(req: HttpRequest) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_some() {
        return HttpResponse::Found().append_header(("Location", "/")).body("");
    }
    
    let content = format!(r#"
      <div class="container">
        <div class="main" style="margin-left: 0; max-width: none; border: none;">
          <div class="form-container" style="margin-top: 50px;">
            <h1 class="form-title">Log in to youbook</h1>
            <form method="post" action="/login_post">
              <input type="text" name="username" placeholder="Username" required>
              <input type="password" name="password" placeholder="Password" required>
              <button type="submit" class="btn btn-primary">Log in</button>
            </form>
            <div class="auth-links">
              Don't have an account? <a href="/register">Sign up</a>
            </div>
          </div>
        </div>
      </div>
    "#);
    
    HttpResponse::Ok().body(layout("Login", &content))
}

#[derive(Deserialize)]
struct LoginForm {
    username: String,
    password: String,
}

async fn login(req: HttpRequest, data: web::Data<AppState>, form: web::Form<LoginForm>) -> HttpResponse {
    println!("[LOGIN] Handling login request for username: {}", form.username);
    let db = data.db.lock().unwrap();
    
    let user: User = match db.query_row(
        "SELECT * FROM users WHERE username = ?",
        params![form.username],
        |row| Ok(User {
            id: row.get(0)?,
            username: row.get(1)?,
            password: row.get(2)?,
            created_at: row.get(3)?,
        })
    ) {
        Ok(u) => u,
        Err(e) => {
            println!("[LOGIN] User not found: {} - error: {:?}", form.username, e);
            return HttpResponse::Unauthorized().body("Invalid credentials");
        }
    };
    
    let valid = verify(&form.password, &user.password).unwrap_or(false);
    println!("[LOGIN] Password verification result: {}", valid);
    
    if !valid {
        println!("[LOGIN] Invalid password for user: {}", form.username);
        return HttpResponse::Unauthorized().body("Invalid credentials");
    }
    
    let session = req.get_session();
    session.insert("userId", user.id).ok();
    let username = user.username.clone();
    session.insert("username", user.username).ok();
    println!("[LOGIN] Session set for user: {} (id: {})", username, user.id);
    
    HttpResponse::Found().append_header(("Location", "/")).body("")
}

async fn register_page(req: HttpRequest) -> HttpResponse {
    let session = req.get_session();
    let user_id: Option<i64> = session.get("userId").ok().flatten();
    
    if user_id.is_some() {
        return HttpResponse::Found().append_header(("Location", "/")).body("");
    }
    
    let content = format!(r#"
      <div class="container">
        <div class="main" style="margin-left: 0; max-width: none; border: none;">
          <div class="form-container" style="margin-top: 50px;">
            <h1 class="form-title">Create account</h1>
            <form method="post" action="/register_post">
              <input type="text" name="username" placeholder="Username" required>
              <input type="password" name="password" placeholder="Password" required>
              <button type="submit" class="btn btn-primary">Sign up</button>
            </form>
            <div class="auth-links">
              Have an account? <a href="/login">Log in</a>
            </div>
          </div>
        </div>
      </div>
    "#);
    
    HttpResponse::Ok().body(layout("Register", &content))
}

async fn register(_req: HttpRequest, data: web::Data<AppState>, form: web::Form<LoginForm>) -> HttpResponse {
    println!("[REGISTER] POST /register handler called!");
    let username = &form.username;
    let password = &form.password;
    
    println!("[REGISTER] Attempting to register user: {}", username);
    
    if username.is_empty() || password.is_empty() {
        return HttpResponse::BadRequest().body("Required");
    }
    
    let hash = match hash(password, DEFAULT_COST) {
        Ok(h) => h,
        Err(_) => return HttpResponse::InternalServerError().body("Error"),
    };
    
    let db = data.db.lock().unwrap();
    let result = db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        params![username, hash]
    );
    
    match result {
        Ok(_) => {
            println!("[REGISTER] User registered successfully: {}", username);
            HttpResponse::Found().append_header(("Location", "/login")).body("")
        }
        Err(e) => {
            println!("[REGISTER] Error registering user: {} - error: {:?}", username, e);
            if e.to_string().contains("UNIQUE") {
                HttpResponse::BadRequest().body("Username exists")
            } else {
                HttpResponse::InternalServerError().body("Error")
            }
        }
    }
}

async fn logout(req: HttpRequest) -> HttpResponse {
    let session = req.get_session();
    session.clear();
    HttpResponse::Found().append_header(("Location", "/")).body("")
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let conn = Connection::open("rustblog.db").unwrap();
    init_db(&conn);
    
    let state = web::Data::new(AppState {
        db: Mutex::new(conn),
    });
    
    println!("\n=== Rust Blog Server ===");
    println!("Blog running at http://localhost:3000\n");
    
    HttpServer::new(move || {
        let key = Key::from("1234567890123456789012345678901234567890123456789012345678901234".as_bytes());
        App::new()
            .app_data(state.clone())
            .wrap(
                SessionMiddleware::builder(
                    CookieSessionStore::default(),
                    key
                )
                .build()
            )
            .service(web::resource("/").to(index))
            .service(web::resource("/my").to(my_posts))
            .service(web::resource("/user/{id}").to(user_posts))
            .service(web::resource("/post/{id}").to(view_post))
            .service(web::resource("/post/{id}").route(web::delete().to(delete_post)))
            .service(web::resource("/post/{id}/comment").to(add_comment))
            .service(web::resource("/post/{id}/like").to(toggle_like))
            .service(web::resource("/post/{id}/share").to(toggle_share))
            .service(web::resource("/posts").to(create_post))
            .service(web::resource("/login").to(login_page))
            .service(web::resource("/login_post").route(web::post().to(login)))
            .service(web::resource("/register").to(register_page))
            .service(web::resource("/register_post").route(web::post().to(register)))
            .service(web::resource("/logout").to(logout))
    })
    .bind("127.0.0.1:3000")?
    .run()
    .await
}
