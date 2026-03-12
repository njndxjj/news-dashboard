const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// 创建临时用户数据目录
const userDataDir = path.join('/tmp', 'openclaw-clean-profile-' + Date.now());
fs.mkdirSync(userDataDir, { recursive: true });

console.log('使用临时配置文件:', userDataDir);

(async () => {
  console.log('启动干净的 Chrome 实例...');

  const browser = await chromium.launch({
    headless: false,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--disable-extensions', '--disable-gpu']
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  console.log('访问网关页面 http://localhost:18789 ...');
  await page.goto('http://localhost:18789', { waitUntil: 'networkidle' });

  // 等待页面完全加载
  await page.waitForTimeout(3000);

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
  await page.waitForTimeout(8000);

  // 截图
  await page.screenshot({ path: '/tmp/openclaw-status-clean.png', fullPage: true });
  console.log('✓ 已保存截图：/tmp/openclaw-status-clean.png');

  console.log('\n浏览器保持打开，请查看 UI 状态');
  console.log('当前 localStorage token:', await page.evaluate(() => localStorage.getItem('gateway-token')));
  console.log('\n清理临时配置文件将在关闭浏览器后自动删除');

  // 保持浏览器打开 120 秒
  await new Promise(resolve => setTimeout(resolve, 120000));

  // 清理临时目录
  try {
    fs.rmSync(userDataDir, { recursive: true, force: true });
    console.log('已清理临时配置文件');
  } catch (e) {
    console.log('清理临时文件失败:', e.message);
  }

  await browser.close();
})().catch(err => {
  console.error('错误:', err);
  // 清理临时目录
  try {
    fs.rmSync(userDataDir, { recursive: true, force: true });
  } catch (e) {}
  process.exit(1);
});
