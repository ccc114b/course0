import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Post() {
  const router = useRouter();
  const { id } = router.query;
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadPost();
    }
  }, [id]);

  const loadPost = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/post/${id}`);
      if (res.ok) {
        const data = await res.json();
        setPost(data);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleDelete = async () => {
    if (!confirm('Delete this post?')) return;
    try {
      await fetch(`/api/post/${id}`, { method: 'DELETE' });
      router.push('/');
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <Link href="/" style={styles.backLink}>← Back</Link>
        <p style={styles.loading}>Loading...</p>
      </div>
    );
  }

  if (!post) {
    return (
      <div style={styles.container}>
        <Link href="/" style={styles.backLink}>← Back</Link>
        <p style={styles.error}>Post not found</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Link href="/" style={styles.backLink}>← Back</Link>
      <h1>{post.title}</h1>
      <p style={styles.meta}>{new Date(post.created_at).toLocaleString()}</p>
      <div 
        style={styles.content} 
        dangerouslySetInnerHTML={{ __html: post.html }} 
      />
      <div style={{ marginTop: '20px' }}>
        <button onClick={handleDelete} style={styles.deleteBtn}>Delete</button>
      </div>
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
  backLink: {
    display: 'inline-block',
    marginBottom: '20px',
    color: '#0066cc',
    textDecoration: 'none',
  },
  meta: {
    color: '#666',
    marginBottom: '20px',
  },
  content: {
    lineHeight: '1.8',
  },
  deleteBtn: {
    background: '#dc3545',
    color: 'white',
    padding: '12px 24px',
    border: 'none',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '14px',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#666',
  },
  error: {
    color: '#dc3545',
  },
};
