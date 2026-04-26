from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown
from database import init_db, get_all_posts, get_post_by_id, create_post

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

def to_dict(row):
    if row:
        return {"id": row["id"], "title": row["title"], "excerpt": row["excerpt"], "created_at": row["created_at"]}
    return None

def to_full_dict(row):
    if row:
        return {"id": row["id"], "title": row["title"], "content": row["content"], "created_at": row["created_at"]}
    return None

@app.get("/", response_class=HTMLResponse)
def home():
    posts = get_all_posts()
    html = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>My Blog</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
    h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
    .post {{ margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
    .post h2 {{ margin-top: 0; }}
    .post a {{ text-decoration: none; color: #333; }}
    .post a:hover {{ color: #0066cc; }}
    .meta {{ color: #666; font-size: 0.9em; }}
    .new-post {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
    input, textarea {{ width: 100%; padding: 10px; margin: 5px 0; box-sizing: border-box; }}
    button {{ background: #333; color: white; padding: 10px 20px; border: none; cursor: pointer; }}
    button:hover {{ background: #555; }}
  </style>
</head>
<body>
  <h1>My Blog</h1>
  <div class="new-post">
    <h3>New Post</h3>
    <form method="post" action="/posts">
      <input type="text" name="title" placeholder="Title" required>
      <textarea name="content" rows="5" placeholder="Content (Markdown supported)" required></textarea>
      <button type="submit">Publish</button>
    </form>
  </div>'''
    for post in posts:
        html += f'''<div class="post">
      <h2><a href="/post/{post['id']}">{post['title']}</a></h2>
      <p class="meta">{post['created_at']}</p>
      <p>{post['excerpt']}...</p>
      <a href="/post/{post['id']}">Read more →</a>
    </div>'''
    html += '</body></html>'
    return html

@app.get("/post/{post_id}", response_class=HTMLResponse)
def get_post(post_id: int):
    post = get_post_by_id(post_id)
    if not post:
        return '<h1>Post not found</h1><a href="/">Back</a>'
    content_html = markdown.markdown(post['content'])
    html = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{post['title']}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
    a {{ color: #333; }}
    .meta {{ color: #666; }}
    .content {{ line-height: 1.8; }}
    .content img {{ max-width: 100%; }}
  </style>
</head>
<body>
  <p><a href="/">← Back</a></p>
  <h1>{post['title']}</h1>
  <p class="meta">{post['created_at']}</p>
  <div class="content">{content_html}</div>
</body></html>'''
    return html

@app.post("/posts")
def add_post(title: str = Form(...), content: str = Form(...)):
    create_post(title, content)
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/", status_code=302)