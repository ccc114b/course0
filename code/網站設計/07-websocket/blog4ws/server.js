const express = require('express');
const bcrypt = require('bcryptjs');
const db = require('./database');
const { WebSocketServer } = require('ws');
const { v4: uuidv4 } = require('uuid');
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

const sessions = new Map();
const clients = new Map();

function broadcast(type, data) {
  const message = JSON.stringify({ type, data });
  clients.forEach((sessionId, ws) => {
    if (ws.readyState === 1) {
      ws.send(message);
    }
  });
}

function getUserPosts(userId, callback) {
  db.all('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id WHERE author_id = ? ORDER BY created_at DESC', [userId], (err, rows) => {
    if (err) return callback(err, []);
    
    if (rows.length === 0) return callback(null, rows);
    
    let processed = 0;
    const postsWithStats = rows.map(post => ({ ...post, comment_count: 0 }));
    
    postsWithStats.forEach((post, index) => {
      db.get('SELECT COUNT(*) as comment_count FROM comments WHERE post_id = ?', [post.id], (err, stats) => {
        if (stats) {
          postsWithStats[index].comment_count = stats.comment_count || 0;
        }
        processed++;
        if (processed === rows.length) {
          callback(null, postsWithStats);
        }
      });
    });
  });
}

function getAllPosts(userId, callback) {
  db.all('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id ORDER BY created_at DESC', [], (err, rows) => {
    if (err) return callback(err, []);
    
    if (rows.length === 0) return callback(null, rows);
    
    let processed = 0;
    const postsWithStats = rows.map(post => ({ ...post, comment_count: 0, like_count: 0, share_count: 0, user_liked: false, user_shared: false }));
    
    postsWithStats.forEach((post, index) => {
      db.get('SELECT (SELECT COUNT(*) FROM comments WHERE post_id = ?) as comment_count, (SELECT COUNT(*) FROM likes WHERE post_id = ?) as like_count, (SELECT COUNT(*) FROM shares WHERE post_id = ?) as share_count', [post.id, post.id, post.id], (err, stats) => {
        if (stats) {
          postsWithStats[index].comment_count = stats.comment_count || 0;
          postsWithStats[index].like_count = stats.like_count || 0;
          postsWithStats[index].share_count = stats.share_count || 0;
        }
        
        if (userId) {
          db.get('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', [post.id, userId], (err, likeRow) => {
            postsWithStats[index].user_liked = !!likeRow;
            
            db.get('SELECT id FROM shares WHERE post_id = ? AND user_id = ?', [post.id, userId], (err, shareRow) => {
              postsWithStats[index].user_shared = !!shareRow;
              
              processed++;
              if (processed === rows.length) {
                callback(null, postsWithStats);
              }
            });
          });
        } else {
          processed++;
          if (processed === rows.length) {
            callback(null, postsWithStats);
          }
        }
      });
    });
  });
}

function getPost(id, callback) {
  db.get('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id WHERE posts.id = ?', [id], (err, row) => {
    callback(err, row);
  });
}

function addPost(content, authorId, callback) {
  db.run('INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)', [content.substring(0, 50), content, authorId], function(err) {
    callback(err, this.lastID);
  });
}

function deletePost(id, userId, callback) {
  db.run('DELETE FROM posts WHERE id = ? AND author_id = ?', [id, userId], function(err) {
    callback(err);
  });
}

function getCommentsByPostId(postId, callback) {
  db.all('SELECT comments.*, users.username FROM comments LEFT JOIN users ON comments.author_id = users.id WHERE post_id = ? ORDER BY created_at DESC', [postId], (err, rows) => {
    callback(err, rows);
  });
}

function addComment(postId, authorId, content, callback) {
  db.run('INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)', [postId, authorId, content], function(err) {
    callback(err, this.lastID);
  });
}

function toggleLike(postId, userId, callback) {
  db.get('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', [postId, userId], (err, row) => {
    if (row) {
      db.run('DELETE FROM likes WHERE post_id = ? AND user_id = ?', [postId, userId], (err) => {
        callback(err, false);
      });
    } else {
      db.run('INSERT INTO likes (post_id, user_id) VALUES (?, ?)', [postId, userId], (err) => {
        callback(err, true);
      });
    }
  });
}

function toggleShare(postId, userId, callback) {
  db.get('SELECT id FROM shares WHERE post_id = ? AND user_id = ?', [postId, userId], (err, row) => {
    if (row) {
      db.run('DELETE FROM shares WHERE post_id = ? AND user_id = ?', [postId, userId], (err) => {
        callback(err, false);
      });
    } else {
      db.run('INSERT INTO shares (post_id, user_id) VALUES (?, ?, ?)', [postId, userId], (err) => {
        callback(err, true);
      });
    }
  });
}

function findUser(username, callback) {
  db.get('SELECT * FROM users WHERE username = ?', [username], (err, row) => {
    callback(err, row);
  });
}

function createUser(username, password, callback) {
  bcrypt.hash(password, 10, (err, hash) => {
    if (err) return callback(err);
    db.run('INSERT INTO users (username, password) VALUES (?, ?)', [username, hash], function(err) {
      callback(err, this.lastID);
    });
  });
}

function getUserById(userId, callback) {
  db.get('SELECT * FROM users WHERE id = ?', [userId], (err, row) => {
    callback(err, row);
  });
}

function handleMessage(ws, message) {
  const { type, data } = message;
  const sessionId = clients.get(ws);
  const userId = sessionId ? sessions.get(sessionId)?.userId : null;
  const username = sessionId ? sessions.get(sessionId)?.username : null;

  switch (type) {
    case 'login': {
      const { username, password } = data;
      findUser(username, (err, user) => {
        if (err || !user) {
          ws.send(JSON.stringify({ type: 'error', data: 'Invalid credentials' }));
          return;
        }
        bcrypt.compare(password, user.password, (err, match) => {
          if (err || !match) {
            ws.send(JSON.stringify({ type: 'error', data: 'Invalid credentials' }));
            return;
          }
          const sessionId = uuidv4();
          sessions.set(sessionId, { userId: user.id, username: user.username });
          clients.set(ws, sessionId);
          ws.send(JSON.stringify({ type: 'login_success', data: { userId: user.id, username: user.username, sessionId } }));
        });
      });
      break;
    }

    case 'register': {
      const { username, password } = data;
      if (!username || !password) {
        ws.send(JSON.stringify({ type: 'error', data: 'Required fields missing' }));
        return;
      }
      createUser(username, password, (err, id) => {
        if (err) {
          if (err.message.includes('UNIQUE')) {
            ws.send(JSON.stringify({ type: 'error', data: 'Username already exists' }));
            return;
          }
          ws.send(JSON.stringify({ type: 'error', data: 'Registration failed' }));
          return;
        }
        ws.send(JSON.stringify({ type: 'register_success', data: true }));
      });
      break;
    }

    case 'get_posts': {
      getAllPosts(userId, (err, posts) => {
        ws.send(JSON.stringify({ type: 'posts', data: posts }));
      });
      break;
    }

    case 'get_my_posts': {
      if (!userId) {
        ws.send(JSON.stringify({ type: 'error', data: 'Not logged in' }));
        return;
      }
      getUserPosts(userId, (err, posts) => {
        ws.send(JSON.stringify({ type: 'my_posts', data: posts }));
      });
      break;
    }

    case 'create_post': {
      if (!userId) {
        ws.send(JSON.stringify({ type: 'error', data: 'Not logged in' }));
        return;
      }
      const { content } = data;
      if (!content) {
        ws.send(JSON.stringify({ type: 'error', data: 'Content required' }));
        return;
      }
      addPost(content, userId, (err, id) => {
        if (err) {
          ws.send(JSON.stringify({ type: 'error', data: 'Failed to create post' }));
          return;
        }
        getAllPosts(userId, (err, posts) => {
          broadcast('posts', posts);
        });
      });
      break;
    }

    case 'delete_post': {
      if (!userId) {
        ws.send(JSON.stringify({ type: 'error', data: 'Not logged in' }));
        return;
      }
      const { postId } = data;
      deletePost(postId, userId, (err) => {
        if (err) {
          ws.send(JSON.stringify({ type: 'error', data: 'Failed to delete' }));
          return;
        }
        getUserPosts(userId, (err, posts) => {
          broadcast('my_posts', posts);
        });
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
        getCommentsByPostId(postId, (err, comments) => {
          const postData = { ...post, comments: comments || [] };
          ws.send(JSON.stringify({ type: 'post_detail', data: postData }));
        });
      });
      break;
    }

    case 'create_comment': {
      if (!userId) {
        ws.send(JSON.stringify({ type: 'error', data: 'Not logged in' }));
        return;
      }
      const { postId, content } = data;
      if (!content) {
        ws.send(JSON.stringify({ type: 'error', data: 'Content required' }));
        return;
      }
      addComment(postId, userId, content, (err, id) => {
        if (err) {
          ws.send(JSON.stringify({ type: 'error', data: 'Failed to create comment' }));
          return;
        }
        getPost(postId, (err, post) => {
          getCommentsByPostId(postId, (err, comments) => {
            broadcast('post_updated', { postId, post, comments: comments || [] });
          });
        });
      });
      break;
    }

    case 'toggle_like': {
      if (!userId) {
        ws.send(JSON.stringify({ type: 'error', data: 'Not logged in' }));
        return;
      }
      const { postId } = data;
      toggleLike(postId, userId, (err, liked) => {
        if (err) {
          ws.send(JSON.stringify({ type: 'error', data: 'Failed to like' }));
          return;
        }
        getAllPosts(userId, (err, posts) => {
          broadcast('posts', posts);
        });
      });
      break;
    }

    case 'toggle_share': {
      if (!userId) {
        ws.send(JSON.stringify({ type: 'error', data: 'Not logged in' }));
        return;
      }
      const { postId } = data;
      toggleShare(postId, userId, (err, shared) => {
        if (err) {
          ws.send(JSON.stringify({ type: 'error', data: 'Failed to share' }));
          return;
        }
        getAllPosts(userId, (err, posts) => {
          broadcast('posts', posts);
        });
      });
      break;
    }

    case 'get_user': {
      const { userId: targetUserId } = data;
      getUserById(targetUserId, (err, user) => {
        if (err || !user) {
          ws.send(JSON.stringify({ type: 'error', data: 'User not found' }));
          return;
        }
        getUserPosts(targetUserId, (err, posts) => {
          ws.send(JSON.stringify({ type: 'user_posts', data: { user, posts } }));
        });
      });
      break;
    }

    case 'logout': {
      const sessionId = clients.get(ws);
      if (sessionId) {
        sessions.delete(sessionId);
        clients.delete(ws);
      }
      ws.send(JSON.stringify({ type: 'logged_out', data: true }));
      break;
    }
  }
}

const server = app.listen(3002, () => {
  console.log('Blog4WS running at http://localhost:3002');
});

const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
  console.log('Client connected');
  
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
    const sessionId = clients.get(ws);
    if (sessionId) {
      sessions.delete(sessionId);
      clients.delete(ws);
    }
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
