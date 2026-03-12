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
  await page.goto('http://localhost:18789', { waitUntil: 'networkidle' });

  console.log('设置 localStorage token...');
  const token = '6a18e607f503da246628896da5649b06dc05446da4c88fd5';

  await page.evaluate((token) => {
    localStorage.setItem('gateway-token', token);
    localStorage.setItem('openclaw-gateway-token', token);
    console.log('Token 已设置:', token);
  }, token);

  // 验证 token 已设置
  const storedToken = await page.evaluate(() => localStorage.getItem('gateway-token'));
  console.log('验证 localStorage token:', storedToken);

  console.log('刷新页面使配置生效...');
  await page.reload({ waitUntil: 'networkidle' });

  console.log('等待 UI 加载...');
  await page.waitForTimeout(5000);

  // 截图
  await page.screenshot({ path: '/tmp/openclaw-with-token.png', fullPage: true });
  console.log('✓ 已保存截图：/tmp/openclaw-with-token.png');

  console.log('\n浏览器保持打开，请查看 UI 状态');
  console.log('当前 localStorage token:', await page.evaluate(() => localStorage.getItem('gateway-token')));

  // 保持浏览器打开 60 秒
  await new Promise(resolve => setTimeout(resolve, 60000));

  await browser.close();
})().catch(err => {
  console.error('错误:', err);
  process.exit(1);
});
