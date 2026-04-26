const { spawn } = require('child_process');
const http = require('http');
const WebSocket = require('ws');
const { JSDOM } = require('jsdom');

const SERVER_PORT = 3003;
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
  assert(html.data.includes('<title>My Blog</title>'), 'HTML contains title');
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

async function testCreatePost() {
  log('Testing post creation...');
  
  const ws = await wsConnect();
  const title = 'Test Post ' + Date.now();
  const content = 'This is test content for the post.';
  
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
          type: 'create_post',
          data: { title, content }
        }));
      }
      
      if (msg.type === 'post_created') {
        ws.send(JSON.stringify({ type: 'get_posts', data: {} }));
      }
      
      if (msg.type === 'posts') {
        const post = msg.data.find(p => p.title === title);
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

async function testGetPost() {
  log('Testing get single post...');
  
  const ws = await wsConnect();
  const title = 'Detail Test Post ' + Date.now();
  const content = 'Content for detail test.';
  
  return new Promise((resolve) => {
    let timeout = setTimeout(() => {
      ws.close();
      assert(false, 'Get post timeout');
      resolve();
    }, 5000);
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      
      if (msg.type === 'connected') {
        ws.send(JSON.stringify({
          type: 'create_post',
          data: { title, content }
        }));
      }
      
      if (msg.type === 'post_created') {
        ws.send(JSON.stringify({ type: 'get_posts', data: {} }));
      }
      
      if (msg.type === 'posts') {
        const post = msg.data.find(p => p.title === title);
        if (post) {
          ws.send(JSON.stringify({ type: 'get_post', data: { postId: post.id } }));
        }
      }
      
      if (msg.type === 'post') {
        assert(msg.data.title === title, 'Single post returns correct data');
        assert(msg.data.html, 'Post includes rendered HTML');
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
  
  const scriptMatch = html.data.match(/<script>([\s\S]*?)<\/script>/);
  assert(scriptMatch, 'Client script exists');
  
  try {
    const script = scriptMatch[1];
    assert(script.includes('WebSocket'), 'Script uses WebSocket');
    assert(script.includes('App.init'), 'App has init');
    assert(script.includes('handleMessage'), 'App has handleMessage');
    assert(script.includes('render'), 'App has render');
    assert(script.includes('createPost'), 'Has createPost handler');
    assert(script.includes('this.render()'), 'App.render() is called in init()');
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
      runScripts: 'dangerously',
      url: `http://localhost:${SERVER_PORT}/`
    });
    
    const { window } = dom;
    const { document } = window;
    
    const title = document.title;
    assert(title === 'My Blog', 'Page title is My Blog');
    
    const h1 = document.querySelector('h1');
    assert(h1 && h1.textContent === 'My Blog', 'H1 heading is rendered');
    
    const form = document.querySelector('form');
    assert(!!form, 'Post form is rendered');
    
    const inputs = document.querySelectorAll('input');
    assert(inputs.length >= 1, 'Title input exists');
    
    const textareas = document.querySelectorAll('textarea');
    assert(textareas.length >= 1, 'Content textarea exists');
    
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
    await testCreatePost();
    await testGetPost();
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
