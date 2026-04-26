const express = require('express');
const session = require('express-session');
const bcrypt = require('bcryptjs');
const db = require('./database');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', 'http://localhost:3001');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  res.header('Access-Control-Allow-Credentials', 'true');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});
app.use(session({
  secret: 'blog-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000 }
}));

app.use((req, res, next) => {
  res.locals.userId = req.session.userId;
  res.locals.username = req.session.username;
  next();
});

function getAllPosts(userId, callback) {
  db.all(`
    SELECT posts.*, users.username 
    FROM posts 
    LEFT JOIN users ON posts.author_id = users.id 
    ORDER BY posts.created_at DESC
  `, [], (err, rows) => {
    if (err) return callback(err, []);

    if (rows.length === 0) return callback(null, rows);

    const postsWithStats = rows.map(post => ({ 
      ...post, 
      comment_count: 0, 
      like_count: 0, 
      share_count: 0, 
      user_liked: false, 
      user_shared: false 
    }));

    let processed = 0;
    postsWithStats.forEach((post, index) => {
      db.get(`SELECT 
        (SELECT COUNT(*) FROM comments WHERE post_id = ?) as comment_count, 
        (SELECT COUNT(*) FROM likes WHERE post_id = ?) as like_count, 
        (SELECT COUNT(*) FROM shares WHERE post_id = ?) as share_count`, 
        [post.id, post.id, post.id], 
        (err, stats) => {
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
        }
      );
    });
  });
}

function getUserPosts(userId, authorId, callback) {
  db.all(`
    SELECT posts.*, users.username 
    FROM posts 
    LEFT JOIN users ON posts.author_id = users.id 
    WHERE author_id = ?
    ORDER BY posts.created_at DESC
  `, [authorId], (err, rows) => {
    if (err) return callback(err, []);

    if (rows.length === 0) return callback(null, rows);

    const postsWithStats = rows.map(post => ({ ...post, comment_count: 0 }));
    
    let processed = 0;
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

function getPost(id, callback) {
  db.get('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id WHERE posts.id = ?', [id], (err, row) => {
    callback(err, row);
  });
}

function getCommentsByPostId(postId, callback) {
  db.all('SELECT comments.*, users.username FROM comments LEFT JOIN users ON comments.author_id = users.id WHERE post_id = ? ORDER BY comments.created_at DESC', [postId], (err, rows) => {
    callback(err, rows);
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
      db.run('INSERT INTO shares (post_id, user_id) VALUES (?, ?)', [postId, userId], (err) => {
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

function getUserById(userId, callback) {
  db.get('SELECT * FROM users WHERE id = ?', [userId], (err, row) => {
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

function requireLogin(req, res, next) {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
}

app.get('/api/me', (req, res) => {
  if (!req.session.userId) {
    return res.json({ user: null });
  }
  res.json({
    user: {
      id: req.session.userId,
      username: req.session.username
    }
  });
});

app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  findUser(username, (err, user) => {
    if (err || !user) return res.status(401).json({ error: 'Invalid credentials' });
    
    bcrypt.compare(password, user.password, (err, match) => {
      if (err || !match) return res.status(401).json({ error: 'Invalid credentials' });
      
      req.session.userId = user.id;
      req.session.username = user.username;
      res.json({ success: true, user: { id: user.id, username: user.username } });
    });
  });
});

app.post('/api/register', (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: 'Required' });
  }

  createUser(username, password, (err, id) => {
    if (err) {
      if (err.message.includes('UNIQUE')) {
        return res.status(400).json({ error: 'Username exists' });
      }
      return res.status(500).json({ error: 'Error' });
    }
    res.json({ success: true });
  });
});

app.post('/api/logout', (req, res) => {
  req.session.destroy();
  res.json({ success: true });
});

app.get('/api/posts', requireLogin, (req, res) => {
  getAllPosts(req.session.userId, (err, posts) => {
    if (err) return res.status(500).json({ error: 'Error' });
    res.json(posts);
  });
});

app.get('/api/my-posts', requireLogin, (req, res) => {
  getUserPosts(req.session.userId, req.session.userId, (err, posts) => {
    if (err) return res.status(500).json({ error: 'Error' });
    res.json(posts);
  });
});

app.get('/api/user/:id/posts', requireLogin, (req, res) => {
  getUserPosts(req.session.userId, req.params.id, (err, posts) => {
    if (err) return res.status(500).json({ error: 'Error' });
    res.json(posts);
  });
});

app.get('/api/user/:id', (req, res) => {
  getUserById(req.params.id, (err, user) => {
    if (err || !user) return res.status(404).json({ error: 'User not found' });
    res.json({ id: user.id, username: user.username });
  });
});

app.post('/api/posts', requireLogin, (req, res) => {
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: 'Content required' });

  addPost(content, req.session.userId, (err, id) => {
    if (err) return res.status(500).json({ error: 'Error saving post' });
    res.json({ success: true, id });
  });
});

app.delete('/api/post/:id', requireLogin, (req, res) => {
  deletePost(req.params.id, req.session.userId, (err) => {
    if (err) return res.status(500).json({ error: 'Error' });
    res.json({ success: true });
  });
});

app.get('/api/post/:id', requireLogin, (req, res) => {
  getPost(req.params.id, (err, post) => {
    if (err || !post) return res.status(404).json({ error: 'Post not found' });

    getCommentsByPostId(req.params.id, (err, comments) => {
      if (err) comments = [];

      db.get('SELECT COUNT(*) as count FROM likes WHERE post_id = ?', [req.params.id], (err, likeRow) => {
        const likeCount = likeRow ? likeRow.count : 0;
        
        db.get('SELECT COUNT(*) as count FROM shares WHERE post_id = ?', [req.params.id], (err, shareRow) => {
          const shareCount = shareRow ? shareRow.count : 0;

          db.get('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', [req.params.id, req.session.userId], (err, userLike) => {
            db.get('SELECT id FROM shares WHERE post_id = ? AND user_id = ?', [req.params.id, req.session.userId], (err, userShare) => {
              res.json({
                ...post,
                like_count: likeCount,
                share_count: shareCount,
                comment_count: comments.length,
                user_liked: !!userLike,
                user_shared: !!userShare,
                comments
              });
            });
          });
        });
      });
    });
  });
});

app.post('/api/post/:id/comment', requireLogin, (req, res) => {
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: 'Content required' });

  addComment(req.params.id, req.session.userId, content, (err, id) => {
    if (err) return res.status(500).json({ error: 'Error saving comment' });
    res.json({ success: true, id });
  });
});

app.post('/api/post/:id/like', requireLogin, (req, res) => {
  toggleLike(req.params.id, req.session.userId, (err, liked) => {
    if (err) return res.status(500).json({ error: 'Error' });
    db.get('SELECT COUNT(*) as count FROM likes WHERE post_id = ?', [req.params.id], (err, likeRow) => {
      const likeCount = likeRow ? likeRow.count : 0;
      res.json({ success: true, liked, like_count: likeCount });
    });
  });
});

app.post('/api/post/:id/share', requireLogin, (req, res) => {
  toggleShare(req.params.id, req.session.userId, (err, shared) => {
    if (err) return res.status(500).json({ error: 'Error' });
    db.get('SELECT COUNT(*) as count FROM shares WHERE post_id = ?', [req.params.id], (err, shareRow) => {
      const shareCount = shareRow ? shareRow.count : 0;
      res.json({ success: true, shared, share_count: shareCount });
    });
  });
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(3001, () => {
  console.log('Blog SPA running at http://localhost:3001');
});
