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

  const token = '6a18e607f503da246628896da5649b06dc05446da4c88fd5';

  // 尝试点击设置按钮
  console.log('尝试打开设置面板...');

  // 等待页面加载
  await page.waitForTimeout(3000);

  // 尝试寻找设置按钮并点击
  try {
    // 尝试多种可能的设置选择器
    await page.click('button:has-text("配置")').catch(() => {});
    await page.waitForTimeout(2000);

    // 或者尝试直接点击左下角的设置图标
    await page.click('[aria-label="settings"]').catch(() => {});
    await page.waitForTimeout(2000);

    // 或者尝试点击侧边栏的设置
    await page.click('text=设置').catch(() => {});
    await page.waitForTimeout(2000);

    console.log('已尝试打开设置面板');
  } catch (e) {
    console.log('无法自动打开设置面板:', e.message);
  }

  // 设置 localStorage
  console.log('设置 localStorage token...');
  await page.evaluate((token) => {
    localStorage.setItem('gateway-token', token);
    localStorage.setItem('openclaw-gateway-token', token);
    // 也尝试设置 sessionStorage
    sessionStorage.setItem('gateway-token', token);
    sessionStorage.setItem('openclaw-gateway-token', token);
  }, token);

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
