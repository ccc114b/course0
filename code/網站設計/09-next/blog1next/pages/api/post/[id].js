import { getPost, deletePost } from '../../../lib/db';
import { marked } from 'marked';

export default function handler(req, res) {
  const { id } = req.query;

  if (req.method === 'GET') {
    getPost(id, (err, post) => {
      if (err || !post) return res.status(404).json({ error: 'Post not found' });
      post.html = marked.parse(post.content);
      res.json(post);
    });
  } else if (req.method === 'DELETE') {
    deletePost(id, (err) => {
      if (err) return res.status(500).json({ error: 'Error deleting post' });
      res.json({ success: true });
    });
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
