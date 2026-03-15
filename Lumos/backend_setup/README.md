# 后端部署指南（含外网发布）

这个后端项目基于 Flask 构建，支持从 RSS 和常见门户网站收集数据。

## 部署方法

### 一、准备工作
1. **安装 Python 环境**
   - 请确保已安装 Python 3.8 或以上版本。
   - 更新 pip: `pip install --upgrade pip`

2. **安装依赖库**
   在 `backend_setup` 目录下运行：

```bash
pip install flask flask_cors feedparser requests beautifulsoup4
```

3. **检查配置**
   - 确保 `server.py` 和 `rss_parser.py` 中的 RSS 和门户网站 URL 配置正确。

### 二、本地运行服务
使用下面的命令启动服务：

```bash
cd backend_setup
python3 server.py
```

服务会默认运行在 `http://127.0.0.1:5000`

### 三、开启外网访问（使用 ngrok 推荐）

1. [下载并安装 ngrok](https://ngrok.com/download)。
2. 启动 ngrok 服务以使本地服务器公开：

```bash
ngrok http 5000
```

3. ngrok 会生成一个公网可访问的 URL，例如：
   - `https://abcd1234.ngrok.io`

4. 将这个地址提供给需要访问的用户。

---

根据需要，还可以将应用程序部署到云服务器（例如 AWS、阿里云、腾讯云）以实现长期外网访问。