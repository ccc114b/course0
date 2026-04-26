const http = require('http');

async function test() {
  let cookie = '';
  
  // Helper to make requests with cookie
  const api = async (method, path, body = null) => {
    return new Promise((resolve, reject) => {
      const headers = { 'Content-Type': 'application/json' };
      if (cookie) headers['Cookie'] = cookie;
      
      const opts = { hostname: 'localhost', port: 3001, path, method, headers };
      const req = http.request(opts, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          // Save cookie from Set-Cookie header
          const setCookie = res.headers['set-cookie'];
          if (setCookie) {
            cookie = setCookie[0].split(';')[0];
            console.log('Cookie updated:', cookie);
          }
          
          console.log(`${method || 'GET'} ${path} => ${res.statusCode}`);
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

  // Test 1: Register
  console.log('=== Test 1: Register ===');
  await api('POST', '/api/register', { username: 'apitest', password: 'pass123' });
  
  // Test 2: Login
  console.log('\n=== Test 2: Login ===');
  const login = await api('POST', '/api/login', { username: 'apitest', password: 'pass123' });
  console.log('Login result:', login.data);
  
  // Test 3: Create post
  console.log('\n=== Test 3: Create post ===');
  const post = await api('POST', '/api/posts', { content: 'Test post from API' });
  console.log('Create post result:', post.data);
  
  // Test 4: Get posts
  console.log('\n=== Test 4: Get posts ===');
  const posts = await api('GET', '/api/posts');
  console.log('Posts count:', posts.data.length);
  const testPost = posts.data.find(p => p.content === 'Test post from API');
  console.log('Test post:', testPost?.id);
  
  // Test 5: Create comment
  console.log('\n=== Test 5: Create comment ===');
  if (testPost) {
    const comment = await api('POST', `/api/post/${testPost.id}/comment`, { content: 'Test reply' });
    console.log('Comment result:', comment.data);
    
    // Test 6: Get post with comments
    console.log('\n=== Test 6: Get post with comments ===');
    const fullPost = await api('GET', `/api/post/${testPost.id}`);
    console.log('Comments count:', fullPost.data.comments?.length);
  }
  
  console.log('\n=== All API tests passed! ===');
}

test().catch(console.error);
