import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const router = useRouter();

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const res = await fetch('/api/posts');
      const data = await res.json();
      setPosts(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    try {
      await fetch('/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
      });
      setTitle('');
      setContent('');
      loadPosts();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>My Blog</h1>
      
      <div style={styles.newPost}>
        <h3>New Post</h3>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={styles.input}
            required
          />
          <textarea
            placeholder="Content (Markdown supported)"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            style={styles.textarea}
            required
          />
          <button type="submit" style={styles.button}>Publish</button>
        </form>
      </div>

      {posts.length === 0 ? (
        <p style={styles.empty}>No posts yet. Create one above!</p>
      ) : (
        posts.map((post) => (
          <div key={post.id} style={styles.post}>
            <h2>
              <Link href={`/post/${post.id}`} style={styles.postLink}>
                {post.title}
              </Link>
            </h2>
            <p style={styles.meta}>{new Date(post.created_at).toLocaleString()}</p>
            <p style={styles.excerpt}>{post.excerpt}...</p>
            <Link href={`/post/${post.id}`} style={styles.readMore}>
              Read more →
            </Link>
          </div>
        ))
      )}
    </div>
  );
}

const styles = {
  container: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    background: '#fafafa',
    minHeight: '100vh',
  },
  header: {
    borderBottom: '2px solid #333',
    paddingBottom: '10px',
  },
  newPost: {
    background: '#fff',
    padding: '25px',
    borderRadius: '8px',
    marginBottom: '30px',
    border: '1px solid #ddd',
  },
  input: {
    width: '100%',
    padding: '12px',
    margin: '8px 0',
    boxSizing: 'border-box',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
  },
  textarea: {
    width: '100%',
    padding: '12px',
    margin: '8px 0',
    boxSizing: 'border-box',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    minHeight: '120px',
    fontFamily: 'inherit',
  },
  button: {
    background: '#333',
    color: 'white',
    padding: '12px 24px',
    border: 'none',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '14px',
  },
  post: {
    marginBottom: '30px',
    padding: '20px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    background: '#fff',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
  },
  postLink: {
    textDecoration: 'none',
    color: '#333',
    cursor: 'pointer',
  },
  meta: {
    color: '#666',
    fontSize: '0.9em',
    marginBottom: '10px',
  },
  excerpt: {
    color: '#555',
    lineHeight: '1.6',
  },
  readMore: {
    color: '#0066cc',
    textDecoration: 'none',
    cursor: 'pointer',
  },
  empty: {
    textAlign: 'center',
    padding: '40px',
    color: '#666',
  },
};
