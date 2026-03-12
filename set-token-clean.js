// OpenClaw Token Setter - Clean Version (使用环境变量)
// 用法：OPENCLAW_TOKEN=your_token node set-token-clean.js
const { chromium } = require('playwright');

// 从环境变量读取 Token
const TOKEN = process.env.OPENCLAW_TOKEN;
if (!TOKEN) {
  console.error('❌ 错误：请设置环境变量 OPENCLAW_TOKEN');
  console.error('用法：OPENCLAW_TOKEN=your_token node set-token-clean.js');
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
  await page.goto('http://localhost:18789');

  console.log('清除旧的 localStorage token...');
  await page.evaluate(() => {
    localStorage.removeItem('gateway-token');
    localStorage.removeItem('openclaw-gateway-token');
  });

  console.log('等待 5 秒让系统重置限流...');
  await page.waitForTimeout(5000);

  console.log('设置新的 localStorage token...');
  await page.evaluate((token) => {
    localStorage.setItem('gateway-token', token);
    localStorage.setItem('openclaw-gateway-token', token);
  }, TOKEN);

  console.log('刷新页面...');
  await page.reload({ waitUntil: 'networkidle' });

  console.log('等待 UI 加载...');
  await page.waitForTimeout(5000);

  // 截图
  await page.screenshot({ path: '/tmp/openclaw-status.png' });
  console.log('✓ 已保存截图：/tmp/openclaw-status.png');

  console.log('\n浏览器保持打开，请查看 UI 状态');
  console.log('如需检查 localStorage，可在 Console 运行：localStorage.getItem("gateway-token")');

  // 保持浏览器打开 60 秒
  await new Promise(resolve => setTimeout(resolve, 60000));

  await browser.close();
})().catch(err => {
  console.error('错误:', err);
  process.exit(1);
});
