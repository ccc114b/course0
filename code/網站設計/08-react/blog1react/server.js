const express = require('express');
const db = require('./database');
const marked = require('marked');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

function getPosts(callback) {
  db.all('SELECT id, title, substr(content, 1, 200) as excerpt, created_at FROM posts ORDER BY created_at DESC', [], (err, rows) => {
    callback(err, rows);
  });
}

function getPost(id, callback) {
  db.get('SELECT * FROM posts WHERE id = ?', [id], (err, row) => {
    callback(err, row);
  });
}

function addPost(title, content, callback) {
  db.run('INSERT INTO posts (title, content) VALUES (?, ?)', [title, content], function(err) {
    callback(err, this.lastID);
  });
}

function deletePost(id, callback) {
  db.run('DELETE FROM posts WHERE id = ?', [id], function(err) {
    callback(err);
  });
}

// CORS headers
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', 'http://localhost:3003');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  res.header('Access-Control-Allow-Credentials', 'true');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// API endpoints
app.get('/api/posts', (req, res) => {
  getPosts((err, posts) => {
    if (err) return res.status(500).json({ error: 'Error loading posts' });
    res.json(posts);
  });
});

app.get('/api/post/:id', (req, res) => {
  getPost(req.params.id, (err, post) => {
    if (err || !post) return res.status(404).json({ error: 'Post not found' });
    post.html = marked.parse(post.content);
    res.json(post);
  });
});

app.post('/api/posts', (req, res) => {
  const { title, content } = req.body;
  if (!title || !content) return res.status(400).json({ error: 'Title and content required' });

  addPost(title, content, (err, id) => {
    if (err) return res.status(500).json({ error: 'Error saving post' });
    res.json({ success: true, id });
  });
});

app.delete('/api/post/:id', (req, res) => {
  deletePost(req.params.id, (err) => {
    if (err) return res.status(500).json({ error: 'Error deleting post' });
    res.json({ success: true });
  });
});

// Serve SPA for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(3003, () => {
  console.log('Blog React running at http://localhost:3003');
});
