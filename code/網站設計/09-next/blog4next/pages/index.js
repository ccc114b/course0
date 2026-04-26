import { useState, useEffect, useRef } from 'react';

export default function Home() {
  const [ws, setWs] = useState(null);
  const [page, setPage] = useState('login');
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [myPosts, setMyPosts] = useState([]);
  const [currentPost, setCurrentPost] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [error, setError] = useState(null);
  const [mounted, setMounted] = useState(false);
  const wsRef = useRef(null);
  const currentPostRef = useRef(null);
  const pageRef = useRef('login');
  const userRef = useRef(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    currentPostRef.current = currentPost;
    pageRef.current = page;
    userRef.current = user;
  }, [currentPost, page, user]);

  useEffect(() => {
    if (mounted) {
      connectWebSocket();
    }
  }, [mounted]);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const websocket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    websocket.onopen = () => {
      console.log('Connected to WebSocket');
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    websocket.onclose = () => {
      console.log('Disconnected, reconnecting...');
      setTimeout(() => connectWebSocket(), 2000);
    };

    websocket.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    wsRef.current = websocket;
    setWs(websocket);
  };

  const send = (type, data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    }
  };

  const handleMessage = (message) => {
    const { type, data } = message;
    
    switch (type) {
      case 'connected':
        if (userRef.current) {
          send('get_posts', {});
        }
        break;
      case 'login_success':
        setUser(data);
        setPage('public');
        send('get_posts', {});
        break;
      case 'register_success':
        setPage('login');
        break;
      case 'error':
        setError(data);
        break;
      case 'posts':
        setPosts(data);
        break;
      case 'my_posts':
        setMyPosts(data);
        break;
      case 'post_detail':
        setCurrentPost(data);
        setPage('post');
        break;
      case 'post_updated':
        if (currentPostRef.current && (currentPostRef.current.id === data.postId || currentPostRef.current.id === data.post?.id)) {
          setCurrentPost({ ...data.post, comments: data.comments });
        }
        break;
      case 'user_posts':
        setCurrentUser(data.user);
        setPosts(data.posts);
        setPage('user');
        break;
      case 'logged_out':
        setUser(null);
        setPage('login');
        break;
    }
  };

  const login = (username, password) => {
    send('login', { username, password });
  };

  const register = (username, password) => {
    send('register', { username, password });
  };

  const logout = () => {
    send('logout', {});
  };

  const createPost = (content) => {
    send('create_post', { content });
  };

  const deletePost = (postId) => {
    send('delete_post', { postId });
  };

  const viewPost = (postId) => {
    send('get_post', { postId });
  };

  const createComment = (postId, content) => {
    send('create_comment', { postId, content });
  };

  const toggleLike = (postId) => {
    send('toggle_like', { postId });
  };

  const toggleShare = (postId) => {
    send('toggle_share', { postId });
  };

  const viewUser = (userId) => {
    send('get_user', { userId });
  };

  const navigate = (newPage) => {
    setError(null);
    
    if (newPage === 'public') {
      send('get_posts', {});
    } else if (newPage === 'my') {
      send('get_my_posts', {});
    } else if (newPage === 'login' || newPage === 'register') {
      setUser(null);
    }
    
    setPage(newPage);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  if (!mounted) {
    return (
      <div className="container">
        <div className="sidebar">
          <div className="logo">youbook</div>
        </div>
        <div className="main" style={{marginLeft: 280}}>
          <div className="loading">Loading...</div>
        </div>
      </div>
    );
  }

  if (!user && page !== 'login' && page !== 'register') {
    return <LoginPage onLogin={() => {}} onNavigate={navigate} error={error} />;
  }

  if (!user) {
    return page === 'register' 
      ? <RegisterPage onRegister={register} onNavigate={navigate} error={error} />
      : <LoginPage onLogin={login} onNavigate={navigate} error={error} />;
  }

  return (
    <div className="container">
      <Sidebar 
        user={user} 
        currentPage={page} 
        onNavigate={navigate} 
        onLogout={logout}
        onViewUser={viewUser}
      />
      <MainContent 
        page={page}
        posts={posts}
        myPosts={myPosts}
        currentPost={currentPost}
        currentUser={currentUser}
        user={user}
        onNavigate={navigate}
        onCreatePost={createPost}
        onDeletePost={deletePost}
        onViewPost={viewPost}
        onCreateComment={createComment}
        onToggleLike={toggleLike}
        onToggleShare={toggleShare}
        onViewUser={viewUser}
        formatDate={formatDate}
      />
    </div>
  );
}

function Sidebar({ user, currentPage, onNavigate, onLogout, onViewUser }) {
  if (!user) {
    return (
      <div className="sidebar">
        <div className="logo" onClick={() => onNavigate('public')}>youbook</div>
        <div className={`nav-item ${currentPage === 'login' ? 'active' : ''}`} onClick={() => onNavigate('login')}>Login</div>
        <div className={`nav-item ${currentPage === 'register' ? 'active' : ''}`} onClick={() => onNavigate('register')}>Register</div>
      </div>
    );
  }

  return (
    <div className="sidebar">
      <div className="logo" onClick={() => onNavigate('public')}>youbook</div>
      <div className={`nav-item ${currentPage === 'public' ? 'active' : ''}`} onClick={() => onNavigate('public')}>Public</div>
      <div className={`nav-item ${currentPage === 'my' ? 'active' : ''}`} onClick={() => onNavigate('my')}>My Posts</div>
      
      <div className="user-profile" onClick={() => onViewUser(user.userId)}>
        <div className="avatar">{user.username[0].toUpperCase()}</div>
        <div className="user-info">
          <div className="user-name">{user.username}</div>
          <div className="user-handle">@{user.username}</div>
        </div>
      </div>
      <div className="nav-item" style={{marginTop: 20}} onClick={onLogout}>Log out</div>
    </div>
  );
}

function MainContent({ page, posts, myPosts, currentPost, currentUser, user, onNavigate, onCreatePost, onDeletePost, onViewPost, onCreateComment, onToggleLike, onToggleShare, onViewUser, formatDate }) {
  let content;

  switch (page) {
    case 'public':
      content = <PostList posts={posts} user={user} onViewPost={onViewPost} onToggleLike={onToggleLike} onToggleShare={onToggleShare} onDeletePost={onDeletePost} onViewUser={onViewUser} formatDate={formatDate} />;
      break;
    case 'my':
      content = (
        <MyPosts 
          posts={myPosts} 
          user={user} 
          onCreatePost={onCreatePost} 
          onDeletePost={onDeletePost} 
          onViewPost={onViewPost}
          onViewUser={onViewUser}
          formatDate={formatDate}
        />
      );
      break;
    case 'post':
      content = (
        <PostDetail 
          post={currentPost} 
          user={user} 
          onNavigate={onNavigate}
          onCreateComment={onCreateComment}
          onViewUser={onViewUser}
          formatDate={formatDate}
        />
      );
      break;
    case 'user':
      content = (
        <UserPosts 
          user={currentUser} 
          posts={posts} 
          onNavigate={onNavigate}
          onViewPost={onViewPost}
          formatDate={formatDate}
        />
      );
      break;
    default:
      content = <PostList posts={posts} user={user} onViewPost={onViewPost} onToggleLike={onToggleLike} onToggleShare={onToggleShare} onDeletePost={onDeletePost} onViewUser={onViewUser} formatDate={formatDate} />;
  }

  return <div className="main">{content}</div>;
}

function LoginPage({ onLogin, onNavigate, error }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <div className="container">
      <Sidebar user={null} currentPage="login" onNavigate={onNavigate} onLogout={() => {}} onViewUser={() => {}} />
      <div className="main" style={{marginLeft: 280}}>
        <div className="form-container" style={{marginTop: 50}}>
          <h1 className="form-title">Log in to youbook</h1>
          <form onSubmit={handleSubmit}>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="submit" className="btn btn-primary">Log in</button>
          </form>
          {error && <div className="error">{error}</div>}
          <div className="auth-links">
            Don't have an account? <a onClick={() => onNavigate('register')}>Sign up</a>
          </div>
        </div>
      </div>
    </div>
  );
}

function RegisterPage({ onRegister, onNavigate, error }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onRegister(username, password);
  };

  return (
    <div className="container">
      <Sidebar user={null} currentPage="register" onNavigate={onNavigate} onLogout={() => {}} onViewUser={() => {}} />
      <div className="main" style={{marginLeft: 280}}>
        <div className="form-container" style={{marginTop: 50}}>
          <h1 className="form-title">Create account</h1>
          <form onSubmit={handleSubmit}>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="submit" className="btn btn-primary">Sign up</button>
          </form>
          {error && <div className="error">{error}</div>}
          <div className="auth-links">
            Have an account? <a onClick={() => onNavigate('login')}>Log in</a>
          </div>
        </div>
      </div>
    </div>
  );
}

function PostList({ posts, user, onViewPost, onToggleLike, onToggleShare, onDeletePost, onViewUser, formatDate }) {
  return (
    <>
      <div className="header">
        <h1>Public Posts</h1>
      </div>
      {posts.length === 0 
        ? <div className="empty-state">No posts yet.</div>
        : posts.map(post => (
            <PostItem 
              key={post.id} 
              post={post} 
              user={user}
              isOwner={user && post.author_id === user.userId}
              onViewPost={onViewPost}
              onToggleLike={onToggleLike}
              onToggleShare={onToggleShare}
              onDeletePost={onDeletePost}
              onViewUser={onViewUser}
              formatDate={formatDate}
            />
          ))
      }
    </>
  );
}

function MyPosts({ posts, user, onCreatePost, onDeletePost, onViewPost, onViewUser, formatDate }) {
  const [content, setContent] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (content.trim()) {
      onCreatePost(content);
      setContent('');
    }
  };

  return (
    <>
      <div className="header">
        <h1>My Posts</h1>
      </div>
      <div className="post-form">
        <form onSubmit={handleSubmit}>
          <textarea 
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What is on your mind?" 
            required
          />
          <div className="post-form-actions">
            <button type="submit" className="btn btn-primary">Post</button>
          </div>
        </form>
      </div>
      {posts.length === 0 
        ? <div className="empty-state">No posts yet. Share something!</div>
        : posts.map(post => (
            <PostItem 
              key={post.id} 
              post={post} 
              user={user}
              isOwner={true}
              onViewPost={onViewPost}
              onDeletePost={onDeletePost}
              onViewUser={onViewUser}
              formatDate={formatDate}
            />
          ))
      }
    </>
  );
}

function PostItem({ post, user, isOwner, onViewPost, onToggleLike, onToggleShare, onDeletePost, onViewUser, formatDate }) {
  const handleClick = (e) => {
    if (e.target.closest('.post-action') || e.target.closest('.delete-btn') || e.target.closest('a')) return;
    onViewPost(post.id);
  };

  return (
    <div className="post" onClick={handleClick}>
      <div className="post-header">
        <div className="post-avatar">{(post.username || '?')[0].toUpperCase()}</div>
        <div className="post-user-info">
          <span className="post-name">
            <a onClick={(e) => { e.stopPropagation(); onViewUser(post.author_id); }}>
              {post.username || 'Unknown'}
            </a>
          </span>
          <span className="post-handle">@{post.username || 'unknown'}</span>
          <span className="post-time"> · {formatDate(post.created_at)}</span>
        </div>
        {isOwner && (
          <span className="delete-btn" onClick={(e) => { e.stopPropagation(); if(confirm('Delete this post?')) onDeletePost(post.id); }}>✕</span>
        )}
      </div>
      <div className="post-content">{post.content}</div>
      <div className="post-actions">
        <div className={`post-action ${post.user_liked ? 'liked' : ''}`} onClick={(e) => { e.stopPropagation(); onToggleLike(post.id); }}>
          <span>{post.user_liked ? '❤️' : '🤍'}</span>
          <span>{post.like_count || 0}</span>
        </div>
        <div className="post-action" onClick={(e) => { e.stopPropagation(); onViewPost(post.id); }}>
          <span>💬</span>
          <span>{post.comment_count || 0}</span>
        </div>
        <div className={`post-action ${post.user_shared ? 'shared' : ''}`} onClick={(e) => { e.stopPropagation(); onToggleShare(post.id); }}>
          <span>{post.user_shared ? '🔄' : '↗️'}</span>
          <span>{post.share_count || 0}</span>
        </div>
      </div>
    </div>
  );
}

function PostDetail({ post, user, onNavigate, onCreateComment, onViewUser, formatDate }) {
  const [comment, setComment] = useState('');

  if (!post) {
    return <div className="loading">Loading...</div>;
  }

  const comments = post.comments || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (comment.trim()) {
      onCreateComment(post.id, comment);
      setComment('');
    }
  };

  return (
    <>
      <div className="back-link" onClick={() => onNavigate('public')}>← Back</div>
      <div className="post">
        <div className="post-header">
          <div className="post-avatar">{(post.username || '?')[0].toUpperCase()}</div>
          <div className="post-user-info">
            <span className="post-name">
              <a onClick={() => onViewUser(post.author_id)}>{post.username || 'Unknown'}</a>
            </span>
            <span className="post-handle">@{post.username || 'unknown'}</span>
            <span className="post-time"> · {formatDate(post.created_at)}</span>
          </div>
        </div>
        <div className="post-content" style={{fontSize: 20}}>{post.content}</div>
      </div>
      {user ? (
        <div className="comment-form">
          <form onSubmit={handleSubmit}>
            <textarea 
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Write a reply..." 
              required
            />
            <div className="post-form-actions">
              <button type="submit" className="btn btn-primary">Reply</button>
            </div>
          </form>
        </div>
      ) : (
        <div className="empty-state"><a onClick={() => onNavigate('login')}>Log in</a> to reply to this post.</div>
      )}
      <div className="header">
        <h1>Replies</h1>
      </div>
      {comments.length === 0 
        ? <div className="empty-state">No replies yet.</div>
        : comments.map(comment => (
            <div key={comment.id} className="comment">
              <div className="comment-header">
                <div className="post-avatar">{(comment.username || '?')[0].toUpperCase()}</div>
                <div className="post-user-info">
                  <span className="post-name">
                    <a onClick={() => onViewUser(comment.author_id)}>{comment.username || 'Unknown'}</a>
                  </span>
                  <span className="post-handle">@{comment.username || 'unknown'}</span>
                  <span className="post-time"> · {formatDate(comment.created_at)}</span>
                </div>
              </div>
              <div className="comment-content">{comment.content}</div>
            </div>
          ))
      }
    </>
  );
}

function UserPosts({ user, posts, onNavigate, onViewPost, formatDate }) {
  if (!user) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <>
      <div className="back-link" onClick={() => onNavigate('public')}>← Back</div>
      <div className="header">
        <h1>@{user.username}'s Posts</h1>
      </div>
      {posts.length === 0 
        ? <div className="empty-state">No posts yet.</div>
        : posts.map(post => (
            <div key={post.id} className="post" onClick={() => onViewPost(post.id)}>
              <div className="post-header">
                <div className="post-avatar">{user.username[0].toUpperCase()}</div>
                <div className="post-user-info">
                  <span className="post-name">
                    <a onClick={(e) => { e.stopPropagation(); onViewUser(user.id); }}>{user.username}</a>
                  </span>
                  <span className="post-handle">@{user.username}</span>
                  <span className="post-time"> · {formatDate(post.created_at)}</span>
                </div>
              </div>
              <div className="post-content">{post.content}</div>
              <div className="post-actions">
                <div className="post-action" onClick={(e) => { e.stopPropagation(); onViewPost(post.id); }}>
                  <span>💬</span>
                  <span>{post.comment_count || 0}</span>
                </div>
              </div>
            </div>
          ))
      }
    </>
  );
}
