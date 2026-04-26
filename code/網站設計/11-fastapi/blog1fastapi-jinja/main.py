from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import markdown
from database import init_db, get_all_posts, get_post_by_id, create_post

templates = Jinja2Templates(directory="templates")

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    posts = get_all_posts()
    posts_list = [{"id": p["id"], "title": p["title"], "excerpt": p["excerpt"], "created_at": p["created_at"]} for p in posts]
    return templates.TemplateResponse(request, "index.html", {"posts": posts_list})

@app.get("/post/{post_id}", response_class=HTMLResponse)
def get_post(request: Request, post_id: int):
    post = get_post_by_id(post_id)
    if not post:
        return "<h1>Post not found</h1><a href='/'>Back</a>"
    content_html = markdown.markdown(post["content"])
    return templates.TemplateResponse(request, "post.html", {
        "post": {
            "id": post["id"],
            "title": post["title"],
            "content": content_html,
            "created_at": post["created_at"]
        }
    })

@app.post("/posts")
def add_post(title: str = Form(...), content: str = Form(...)):
    create_post(title, content)
    return RedirectResponse("/", status_code=302)