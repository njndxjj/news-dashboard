const { chromium } = require('playwright');

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
  await page.evaluate(() => {
    localStorage.setItem('gateway-token', '6a18e607f503da246628896da5649b06dc05446da4c88fd5');
    localStorage.setItem('openclaw-gateway-token', '6a18e607f503da246628896da5649b06dc05446da4c88fd5');
  });

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
