// OpenClaw UI Token Setter (使用环境变量)
// 用法：OPENCLAW_TOKEN=your_token node set-token-ui.js
const { chromium } = require('playwright');

const TOKEN = process.env.OPENCLAW_TOKEN;
if (!TOKEN) {
  console.error('❌ 错误：请设置环境变量 OPENCLAW_TOKEN');
  console.error('用法：OPENCLAW_TOKEN=your_token node set-token-ui.js');
  process.exit(1);
}

(async () => {
  console.log('启动 Chrome...');

  const browser = await chromium.launch({
    headless: false,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('访问网关页面 http://localhost:18789 ...');
  await page.goto('http://localhost:18789', { waitUntil: 'networkidle' });

  // 等待页面加载
  await page.waitForTimeout(3000);

  // 设置 localStorage
  console.log('设置 localStorage token...');
  await page.evaluate((token) => {
    localStorage.setItem('gateway-token', token);
    localStorage.setItem('openclaw-gateway-token', token);
    sessionStorage.setItem('gateway-token', token);
    sessionStorage.setItem('openclaw-gateway-token', token);
  }, TOKEN);

  // 验证
  const storedToken = await page.evaluate(() => localStorage.getItem('gateway-token'));
  console.log('验证 localStorage token:', storedToken);

  console.log('刷新页面...');
  await page.reload({ waitUntil: 'networkidle' });

  await page.waitForTimeout(8000);

  // 截图
  await page.screenshot({ path: '/tmp/openclaw-settings.png', fullPage: true });
  console.log('✓ 已保存截图：/tmp/openclaw-settings.png');

  console.log('\n浏览器保持打开');

  // 保持浏览器打开
  await new Promise(resolve => setTimeout(resolve, 120000));

  await browser.close();
})().catch(err => {
  console.error('错误:', err);
  process.exit(1);
});
