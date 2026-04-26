const { spawn } = require('child_process');
const http = require('http');
const WebSocket = require('ws');
const { JSDOM } = require('jsdom');

const SERVER_PORT = 3004;
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
    const ws = new WebSocket(`ws://localhost:${SERVER_PORT}`);
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
      if (data.toString().includes('running')) {
        setTimeout(resolve, 500);
      }
    });
    
    server.on('error', reject);
    setTimeout(() => resolve(), 2000);
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
  assert(html.data.includes('<title>youbook</title>'), 'HTML contains title');
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
  
  const scriptMatch = html.data.match(/<script type="text\/babel">([\s\S]*?)<\/script>/);
  assert(scriptMatch, 'Client React script exists');
  
  try {
    const script = scriptMatch[1];
    assert(script.includes('React'), 'Script uses React');
    assert(script.includes('function App()'), 'App component exists');
    assert(script.includes('useState'), 'Uses React hooks');
    assert(script.includes('useEffect'), 'Uses React hooks');
    assert(script.includes('WebSocket'), 'Script uses WebSocket');
  } catch (err) {
    assert(false, `Client script error: ${err.message}`);
  }
}

async function testBrowserRendering() {
  log('Testing browser rendering with jsdom...');
  
  const response = await httpGet('/');
  const html = response.data;
  
  try {
    const dom = new JSDOM(html, {
      runScripts: 'outside-only',
      url: `http://localhost:${SERVER_PORT}/`
    });
    
    const { window } = dom;
    const { document } = window;
    
    const title = document.title;
    assert(title === 'youbook', 'Page title is youbook');
    
    const rootDiv = document.getElementById('root');
    assert(!!rootDiv, 'Root div exists');
    
    const scripts = document.querySelectorAll('script');
    const hasReact = Array.from(scripts).some(s => s.src && s.src.includes('react'));
    assert(hasReact, 'React scripts are loaded');
    
    window.close();
    
  } catch (err) {
    log(`Browser rendering error: ${err.message}`, 'fail');
    testsFailed++;
  }
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
    await testBrowserRendering();
  } catch (err) {
    log(`Test error: ${err.message}`, 'fail');
    testsFailed++;
  }
  
  await stopServer();
  
  console.log(`\n=== Results: ${testsPassed} passed, ${testsFailed} failed ===\n`);
  process.exit(testsFailed > 0 ? 1 : 0);
}

runTests();
