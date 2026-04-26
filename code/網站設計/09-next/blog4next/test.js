const { spawn } = require('child_process');
const http = require('http');
const WebSocket = require('ws');

const SERVER_PORT = 3005;
const BASE_URL = `http://localhost:${SERVER_PORT}`;

let server;
let testsPassed = 0;
let testsFailed = 0;

function log(msg, type = 'info') {
  const prefix = type === 'pass' ? '✓' : type === 'fail' ? '✗' : '•';
  console.log(`${prefix} ${msg}`);
}

function assert(condition, message) {
  if (condition) {
    testsPassed++;
    log(message, 'pass');
    return true;
  } else {
    testsFailed++;
    log(message, 'fail');
    return false;
  }
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function httpGet(path) {
  return new Promise((resolve, reject) => {
    http.get(`${BASE_URL}${path}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, data }));
    }).on('error', reject);
  });
}

function wsConnect() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://localhost:${SERVER_PORT}/ws`);
    ws.on('open', () => resolve(ws));
    ws.on('error', reject);
  });
}

async function startServer() {
  return new Promise((resolve, reject) => {
    server = spawn('node', ['server.js'], {
      cwd: __dirname,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    server.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('ready') || output.includes('running')) {
        setTimeout(resolve, 2000);
      }
    });
    
    server.on('error', reject);
    setTimeout(() => resolve(), 5000);
  });
}

async function stopServer() {
  if (server) {
    server.kill();
    await wait(500);
  }
}

async function testServerBasic() {
  log('Testing server basic endpoints...');
  
  const html = await httpGet('/');
  assert(html.status === 200, 'GET / returns 200');
  assert(html.data.includes('youbook') || html.data.includes('Youbook'), 'HTML contains app');
}

async function testWebSocketConnection() {
  log('Testing WebSocket connection...');
  
  const ws = await wsConnect();
  assert(ws.readyState === WebSocket.OPEN, 'WebSocket connects successfully');
  
  return new Promise((resolve) => {
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      assert(msg.type === 'connected', 'Server sends connected message');
      ws.close();
      resolve();
    });
  });
}

async function testWebSocketAuth() {
  log('Testing WebSocket authentication...');
  
  const ws = await wsConnect();
  const username = 'testuser_' + Date.now();
  
  return new Promise((resolve) => {
    let timeout = setTimeout(() => {
      ws.close();
      resolve();
    }, 5000);
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      
      if (msg.type === 'connected') {
        ws.send(JSON.stringify({
          type: 'register',
          data: { username, password: 'testpass123' }
        }));
      }
      
      if (msg.type === 'register_success') {
        assert(true, 'User registration works');
        ws.send(JSON.stringify({
          type: 'login',
          data: { username, password: 'testpass123' }
        }));
      }
      
      if (msg.type === 'login_success') {
        assert(msg.data.username === username, 'User login works');
        assert(msg.data.sessionId, 'Session ID is returned');
        clearTimeout(timeout);
        ws.close();
        resolve();
      }
    });
  });
}

async function testCreatePost() {
  log('Testing post creation...');
  
  const ws = await wsConnect();
  const username = 'testuser2_' + Date.now();
  
  return new Promise((resolve) => {
    let timeout = setTimeout(() => {
      ws.close();
      assert(false, 'Post creation timeout');
      resolve();
    }, 5000);
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      
      if (msg.type === 'connected') {
        ws.send(JSON.stringify({
          type: 'register',
          data: { username, password: 'pass123' }
        }));
      }
      
      if (msg.type === 'register_success') {
        ws.send(JSON.stringify({
          type: 'login',
          data: { username, password: 'pass123' }
        }));
      }
      
      if (msg.type === 'login_success') {
        ws.send(JSON.stringify({
          type: 'create_post',
          data: { content: 'Hello from test!' }
        }));
      }
      
      if (msg.type === 'posts') {
        const post = msg.data.find(p => p.content === 'Hello from test!');
        if (post) {
          assert(true, 'Post is created and returned');
          clearTimeout(timeout);
          ws.close();
          resolve();
        }
      }
    });
  });
}

async function testCreateComment() {
  log('Testing comment creation...');
  
  const ws = await wsConnect();
  const username = 'testuser3_' + Date.now();
  
  return new Promise((resolve) => {
    let postId = null;
    let timeout = setTimeout(() => {
      ws.close();
      assert(false, 'Comment creation timeout');
      resolve();
    }, 8000);
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      
      if (msg.type === 'connected') {
        ws.send(JSON.stringify({
          type: 'register',
          data: { username, password: 'pass123' }
        }));
      }
      
      if (msg.type === 'register_success') {
        ws.send(JSON.stringify({
          type: 'login',
          data: { username, password: 'pass123' }
        }));
      }
      
      if (msg.type === 'login_success') {
        ws.send(JSON.stringify({
          type: 'create_post',
          data: { content: 'Post for comment test' }
        }));
      }
      
      if (msg.type === 'posts' && !postId) {
        const post = msg.data.find(p => p.content === 'Post for comment test');
        if (post) {
          postId = post.id;
          ws.send(JSON.stringify({
            type: 'create_comment',
            data: { postId: post.id, content: 'Test comment' }
          }));
        }
      }
      
      if (msg.type === 'post_updated' && postId) {
        const hasComment = msg.data.comments && msg.data.comments.some(c => c.content === 'Test comment');
        assert(hasComment, 'Comment appears in post_updated broadcast');
        
        ws.send(JSON.stringify({
          type: 'get_post',
          data: { postId }
        }));
      }
      
      if (msg.type === 'post_detail') {
        const hasComment = msg.data.comments && msg.data.comments.some(c => c.content === 'Test comment');
        assert(hasComment, 'Comment appears in post_detail after creation');
        
        clearTimeout(timeout);
        ws.close();
        resolve();
      }
    });
  });
}

async function testClientCode() {
  log('Testing client JavaScript code...');
  
  const html = await httpGet('/');
  
  assert(html.data.includes('container') || html.data.includes('sidebar'), 'CSS styles are present');
  assert(html.data.includes('youbook') || html.data.includes('Youbook'), 'App title is present');
}

async function runTests() {
  console.log('\n=== Starting Tests ===\n');
  
  await startServer();
  await wait(1000);
  
  try {
    await testServerBasic();
    await testWebSocketConnection();
    await testWebSocketAuth();
    await testCreatePost();
    await testCreateComment();
    await testClientCode();
  } catch (err) {
    log(`Test error: ${err.message}`, 'fail');
    testsFailed++;
  }
  
  await stopServer();
  
  console.log(`\n=== Results: ${testsPassed} passed, ${testsFailed} failed ===\n`);
  process.exit(testsFailed > 0 ? 1 : 0);
}

runTests();
