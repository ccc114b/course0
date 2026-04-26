const { chromium } = require('playwright');

async function test() {
  console.log('Starting browser test...');
  
  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  let browser;
  try {
    browser = await chromium.launch({ 
      headless: false,
      executablePath: chromePath,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  } catch (e) {
    console.log('Chrome launch failed:', e.message);
    process.exit(1);
  }

  const page = await browser.newPage();
  
  try {
    // Test 1: Load page
    console.log('\n=== Test 1: Load page ===');
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1');
    const title = await page.textContent('h1');
    console.log('Page title:', title);
    
    // Test 2: Create post
    console.log('\n=== Test 2: Create post ===');
    await page.fill('#title', 'Browser Test Post');
    await page.fill('#content', 'This is a test post created from browser automation.');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    
    // Check if post appears
    const postTitle = await page.textContent('.post h2');
    console.log('Post created:', postTitle);
    
    // Test 3: View post
    console.log('\n=== Test 3: View post ===');
    await page.click('.post h2 a');
    await page.waitForTimeout(2000);
    
    const postTitle2 = await page.textContent('#post-title');
    console.log('Viewing post:', postTitle2);
    
    // Test 4: Go back
    console.log('\n=== Test 4: Go back ===');
    await page.click('.back-link');
    await page.waitForTimeout(2000);
    
    const homeTitle = await page.textContent('h1');
    console.log('Back to:', homeTitle);
    
    // Test 5: Create another post
    console.log('\n=== Test 5: Create another post ===');
    await page.fill('#title', 'Second Post');
    await page.fill('#content', 'Another test post.');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    
    const postsCount = await page.locator('.post').count();
    console.log('Posts count:', postsCount);
    
    console.log('\n=== All browser tests passed! ===');
    
  } catch (err) {
    console.error('Test error:', err.message);
    await page.screenshot({ path: 'test_error.png' });
  }
  
  await browser.close();
}

test().catch(console.error);
