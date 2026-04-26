const express = require('express');
const db = require('./database');
const { WebSocketServer } = require('ws');
const marked = require('marked');
const path = require('path');

process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const clients = new Set();

function broadcast(type, data) {
  const message = JSON.stringify({ type, data });
  clients.forEach(ws => {
    if (ws.readyState === 1) {
      ws.send(message);
    }
  });
}

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

function handleMessage(ws, message) {
  const { type, data } = message;

  switch (type) {
    case 'get_posts': {
      getPosts((err, posts) => {
        ws.send(JSON.stringify({ type: 'posts', data: posts }));
      });
      break;
    }

    case 'get_post': {
      const { postId } = data;
      getPost(postId, (err, post) => {
        if (err || !post) {
          ws.send(JSON.stringify({ type: 'error', data: 'Post not found' }));
          return;
        }
        post.html = marked.parse(post.content);
        ws.send(JSON.stringify({ type: 'post', data: post }));
      });
      break;
    }

    case 'create_post': {
      const { title, content } = data;
      if (!title || !content) {
        ws.send(JSON.stringify({ type: 'error', data: 'Title and content required' }));
        return;
      }
      addPost(title, content, (err, id) => {
        if (err) {
          ws.send(JSON.stringify({ type: 'error', data: 'Failed to create post' }));
          return;
        }
        getPosts((err, posts) => {
          broadcast('posts', posts);
          ws.send(JSON.stringify({ type: 'post_created', data: { id } }));
        });
      });
      break;
    }
  }
}

const server = app.listen(3003, () => {
  console.log('Blog1WS running at http://localhost:3003');
});

const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);
  
  ws.on('error', (err) => {
    console.error('WebSocket error:', err);
  });
  
  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      handleMessage(ws, message);
    } catch (err) {
      console.error('Message error:', err);
      ws.send(JSON.stringify({ type: 'error', data: 'Invalid message format' }));
    }
  });

  ws.on('close', () => {
    clients.delete(ws);
    console.log('Client disconnected');
  });

  ws.send(JSON.stringify({ type: 'connected', data: true }));
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.use((err, req, res, next) => {
  console.error('Express error:', err);
  res.status(500).send('Internal Server Error');
});
