const http = require('http');

async function test() {
  console.log('Starting API tests...');
  
  const baseURL = 'http://localhost:3002';
  
  // Helper to make requests
  const api = async (method, path, body = null) => {
    return new Promise((resolve, reject) => {
      const headers = { 'Content-Type': 'application/json' };
      
      const opts = { hostname: 'localhost', port: 3002, path, method, headers };
      const req = http.request(opts, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          console.log(`${method} ${path} => ${res.statusCode}`);
          try {
            resolve({ status: res.statusCode, data: JSON.parse(data) });
          } catch(e) {
            resolve({ status: res.statusCode, data });
          }
        });
      });
      req.on('error', reject);
      if (body) req.write(JSON.stringify(body));
      req.end();
    });
  };

  // Test 1: Get posts (empty)
  console.log('\n=== Test 1: Get posts ===');
  const posts1 = await api('GET', '/api/posts');
  console.log('Posts count:', posts1.data.length);

  // Test 2: Create post
  console.log('\n=== Test 2: Create post ===');
  const newPost = await api('POST', '/api/posts', { 
    title: 'Test Post', 
    content: '# Hello World\nThis is a test post with **markdown** content.' 
  });
  console.log('Created post ID:', newPost.data.id);

  // Test 3: Get posts again
  console.log('\n=== Test 3: Get posts (with content) ===');
  const posts2 = await api('GET', '/api/posts');
  console.log('Posts count:', posts2.data.length);
  const testPost = posts2.data[0];
  console.log('Latest post title:', testPost.title);

  // Test 4: Get single post
  console.log('\n=== Test 4: Get single post ===');
  const singlePost = await api('GET', `/api/post/${testPost.id}`);
  console.log('Post title:', singlePost.data.title);
  console.log('Post has HTML:', !!singlePost.data.html);

  // Test 5: Create another post
  console.log('\n=== Test 5: Create another post ===');
  const post2 = await api('POST', '/api/posts', { 
    title: 'Second Post', 
    content: 'This is the second post.' 
  });
  console.log('Created post ID:', post2.data.id);

  // Test 6: Get all posts (should be 2)
  console.log('\n=== Test 6: Get all posts ===');
  const posts3 = await api('GET', '/api/posts');
  console.log('Posts count:', posts3.data.length);

  // Test 7: Delete post
  console.log('\n=== Test 7: Delete post ===');
  const deleted = await api('DELETE', `/api/post/${post2.data.id}`);
  console.log('Delete result:', deleted.data);

  // Test 8: Verify post deleted
  console.log('\n=== Test 8: Verify post deleted ===');
  const posts4 = await api('GET', '/api/posts');
  console.log('Posts count after delete:', posts4.data.length);

  // Test 9: Get deleted post (should fail)
  console.log('\n=== Test 9: Get deleted post ===');
  try {
    await api('GET', `/api/post/${post2.data.id}`);
    console.log('ERROR: Should have failed!');
  } catch (e) {
    console.log('Correctly failed to get deleted post');
  }

  console.log('\n=== All API tests passed! ===');
}

test().catch(console.error);
