const { chromium } = require('playwright');

(async () => {
  console.log('启动 Chrome 测试无认证模式...');

  const browser = await chromium.launch({
    headless: false,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('访问网关页面 http://localhost:18789 ...');
  await page.goto('http://localhost:18789', { waitUntil: 'networkidle' });

  console.log('等待 UI 加载...');
  await page.waitForTimeout(5000);

  // 截图
  await page.screenshot({ path: '/tmp/openclaw-no-auth.png', fullPage: true });
  console.log('✓ 已保存截图：/tmp/openclaw-no-auth.png');

  console.log('\n浏览器保持打开，请查看 UI 状态');

  // 保持浏览器打开 60 秒
  await new Promise(resolve => setTimeout(resolve, 60000));

  await browser.close();
})().catch(err => {
  console.error('错误:', err);
  process.exit(1);
});
