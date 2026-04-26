const { chromium } = require('playwright');

async function test() {
  console.log('Starting browser test...');
  
  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  let browser = await chromium.launch({ 
    headless: false,
    executablePath: chromePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  page.on('dialog', async dialog => {
    console.log('DIALOG:', dialog.message());
    await dialog.accept();
  });
  
  page.on('console', msg => console.log('CONSOLE:', msg.text()));
  
  try {
    // Load page
    console.log('\n=== Test 1: Load page ===');
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.waitForSelector('#app');
    console.log('Page loaded');
    
    // Register
    console.log('\n=== Test 2: Register ===');
    const uniqueUser = 'test' + Date.now();
    await page.fill('input[placeholder="Username"]', uniqueUser);
    await page.fill('input[placeholder="Password"]', 'pass123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    
    // Login
    console.log('\n=== Test 3: Login ===');
    await page.fill('input[placeholder="Username"]', uniqueUser);
    await page.fill('input[placeholder="Password"]', 'pass123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    console.log('Logged in');
    
    // Navigate to My Posts
    console.log('\n=== Test 4: My Posts ===');
    await page.click('.nav-item:has-text("My Posts")');
    await page.waitForTimeout(2000);
    
    // Create post
    console.log('\n=== Test 5: Create post ===');
    await page.fill('#post-content', 'Test post!');
    await page.click('button:has-text("Post")');
    await page.waitForTimeout(2000);
    console.log('Post created');
    
    // View post
    console.log('\n=== Test 6: View post ===');
    await page.locator('.post').first().click();
    await page.waitForTimeout(2000);
    
    // Add comment via direct API
    console.log('\n=== Test 7: Add comment ===');
    const postId = await page.$eval('button:has-text("Reply")', btn => {
      const m = btn.onclick.toString().match(/createComment\((\d+)\)/);
      return m ? parseInt(m[1]) : null;
    });
    console.log('Post ID:', postId);
    
    await page.fill('#comment-content', 'My test comment');
    
    // Call API directly
    await page.evaluate(async (pid) => {
      await fetch(`/api/post/${pid}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: 'My test comment' }),
        credentials: 'include'
      });
    }, postId);
    
    console.log('Comment API called');
    await page.waitForTimeout(3000);
    
    // Check result
    const comments = await page.locator('.comment').count();
    console.log('Comments found:', comments);
    
    if (comments > 0) {
      console.log('\n=== SUCCESS! ===');
    } else {
      console.log('\n=== FAILED: No comments ===');
    }
    
  } catch (err) {
    console.error('Error:', err.message);
  }
  
  await page.screenshot({ path: 'result.png' });
  await browser.close();
}

test();
