import { getPosts, addPost } from '../../lib/db';

export default function handler(req, res) {
  if (req.method === 'GET') {
    getPosts((err, posts) => {
      if (err) return res.status(500).json({ error: 'Error loading posts' });
      res.json(posts);
    });
  } else if (req.method === 'POST') {
    const { title, content } = req.body;
    if (!title || !content) return res.status(400).json({ error: 'Title and content required' });

    addPost(title, content, (err, id) => {
      if (err) return res.status(500).json({ error: 'Error saving post' });
      res.json({ success: true, id });
    });
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
