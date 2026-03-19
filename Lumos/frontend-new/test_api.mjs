import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

// 监听请求
page.on('request', request => {
  if (request.url().includes('/api/admin/login')) {
    console.log('=== 请求详情 ===');
    console.log('URL:', request.url());
    console.log('Method:', request.method());
    const headers = request.headers();
    console.log('Content-Type:', headers['content-type']);
    console.log('PostData:', request.postData());
  }
});

page.on('response', response => {
  if (response.url().includes('/api/admin/login')) {
    console.log('\n=== 响应详情 ===');
    console.log('Status:', response.status());
    console.log('Method:', response.request().method());
  }
});

await page.goto('http://localhost:5000/admin', { waitUntil: 'networkidle' });
await page.waitForTimeout(500);

// 填写并点击登录
await page.fill('input[placeholder="请输入管理员账号"]', 'admin');
await page.fill('input[type="password"]', 'admin123');
const loginButton = await page.$('button:has-text("登录")');
if (loginButton) {
  console.log('\n点击登录按钮...');
  await loginButton.click();
  await page.waitForTimeout(2000);
}

await browser.close();
