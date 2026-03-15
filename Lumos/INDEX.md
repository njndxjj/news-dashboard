# Lumos 项目文档索引

这是 Lumos 商家洞察系统的完整文档导航，帮助你快速找到所需信息。

---

## 📚 文档列表

### 🎯 核心文档

| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [README.md](README.md) | 项目介绍、特性、技术架构 | 所有人 |
| [QUICKSTART.md](QUICKSTART.md) | 5 分钟快速部署指南 | 新手用户 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 详细架构设计文档 | 开发者、架构师 |

### 🔧 技术文档

| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [API.md](API.md) | 完整 API 接口文档 | 前端开发、后端开发 |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | 开发环境、代码规范、测试 | 开发者 |
| [backend/README.md](backend/README.md) | 后端服务详细说明 | 后端开发 |
| [frontend-new/README.md](frontend-new/README.md) | 前端应用详细说明 | 前端开发 |

### 📋 配置文件

| 文件 | 描述 |
|------|------|
| [config/config.yaml](config/config.yaml) | 平台数据源配置 |
| [config/rss_mapping.yaml](config/rss_mapping.yaml) | RSS 地址映射表 |
| [docker-compose.yml](docker-compose.yml) | Docker 编排配置 |
| [.env.example](.env) | 环境变量模板 |

---

## 🗺️ 使用指南

### 我是新手用户，想快速体验
👉 阅读 [QUICKSTART.md](QUICKSTART.md)，选择 Docker 部署方式，5 分钟即可完成部署。

### 我是开发者，想了解项目架构
👉 阅读 [ARCHITECTURE.md](ARCHITECTURE.md)，了解系统分层、数据流、模块设计。

### 我是前端开发，想修改界面
👉 阅读 [frontend-new/README.md](frontend-new/README.md) 和 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)。

### 我是后端开发，想添加 API
👉 阅读 [backend/README.md](backend/README.md)、[API.md](API.md) 和 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)。

### 我想查看 API 接口
👉 直接查看 [API.md](API.md)，包含所有 REST API 的详细说明。

---

## 📖 阅读顺序建议

### 入门级 (普通用户)
1. [README.md](README.md) - 了解项目
2. [QUICKSTART.md](QUICKSTART.md) - 快速部署
3. 开始使用系统

### 进阶级 (开发者)
1. [README.md](README.md) - 了解项目
2. [ARCHITECTURE.md](ARCHITECTURE.md) - 理解架构
3. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - 开发环境
4. 开始编码

### 专家级 (深度定制)
1. [ARCHITECTURE.md](ARCHITECTURE.md) - 深入架构
2. [API.md](API.md) - API 设计
3. [backend/README.md](backend/README.md) - 后端细节
4. [frontend-new/README.md](frontend-new/README.md) - 前端细节
5. 开始深度定制

---

## 🔍 快速查找

### 想了解系统支持哪些数据源？
📌 查看 [README.md](README.md#-数据源覆盖) 或 [config/config.yaml](config/config.yaml)

### 想知道如何部署？
📌 查看 [QUICKSTART.md](QUICKSTART.md#-部署方式)

### 想了解用户系统如何工作？
📌 查看 [ARCHITECTURE.md](ARCHITECTURE.md#36-用户系统模块) 或 [backend/README.md](backend/README.md#用户认证)

### 想知道如何添加新的爬虫？
📌 查看 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#添加新的数据源)

### 想了解 API 接口详情？
📌 查看 [API.md](API.md)

### 想知道定时任务如何配置？
📌 查看 [backend/README.md](backend/README.md#定时任务) 或 [ARCHITECTURE.md](ARCHITECTURE.md#37-定时任务模块)

### 想了解知识图谱如何工作？
📌 查看 [ARCHITECTURE.md](ARCHITECTURE.md#35-知识图谱模块)

### 想知道如何测试？
📌 查看 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#测试)

---

## 📊 文档统计

| 文档 | 字数 | 最后更新 |
|------|------|----------|
| README.md | ~3000 | 2026-03-15 |
| ARCHITECTURE.md | ~8000 | 2026-03-15 |
| QUICKSTART.md | ~4000 | 2026-03-15 |
| API.md | ~5000 | 2026-03-15 |
| DEVELOPER_GUIDE.md | ~6000 | 2026-03-15 |
| backend/README.md | ~3000 | 2026-03-15 |
| frontend-new/README.md | ~4000 | 2026-03-15 |

---

## 🤝 贡献文档

如果你发现文档有问题或有改进建议：

1. **提交 Issue**: https://github.com/njndxjj/news-dashboard/issues
2. **提交 PR**: Fork 项目 → 修改文档 → 提交 PR

**文档规范**:
- 使用 Markdown 格式
- 标题使用层级结构 (# → ## → ###)
- 代码块使用三重反引号
- 链接使用相对路径

---

## 📞 获取帮助

- **GitHub Issues**: https://github.com/njndxjj/news-dashboard/issues
- **开发团队**: Lumos Team

---

## 📝 文档更新日志

### 2026-03-15 - 文档全面重写
- ✅ 重写 README.md - 重新定位为商家洞察系统
- ✅ 重写 ARCHITECTURE.md - 更新项目背景和技术架构
- ✅ 重写 QUICKSTART.md - 更新快速开始指南
- ✅ 重写 API.md - 更新 API 接口文档
- ✅ 重写 DEVELOPER_GUIDE.md - 更新开发指南
- ✅ 更新 backend/README.md - 后端服务说明
- ✅ 更新 frontend-new/README.md - 前端应用说明
- ✅ 更新 INDEX.md - 文档索引

---

<div align="center">

**Made with ❤️ by Lumos Team**

[⬆ 返回顶部](#lumos-项目文档索引)

</div>

*Lumos Team © 2026*
