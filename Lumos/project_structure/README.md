# 项目结构说明

这是一个基于 PRD 的热点内容聚合咨询平台项目。

## 项目目录
```
.
├── backend         # 后端服务代码（Flask，信息抓取+知识图谱）
├── frontend        # 前端交互界面代码（React.js）
├── database        # 数据库配置与脚本（SQL/图数据库）
├── docs            # 文档（需求文档，接口说明等）
└── tests           # 测试与自动化脚本
```

## 安装与启动
请按照以下步骤进行项目启动：

### 1. 后端
进入 `backend` 目录，安装依赖并启动服务：
```bash
pip install -r requirements.txt
python app_integration.py
```

### 2. 前端
进入 `frontend` 目录，安装依赖并启动开发服务器：
```bash
npm install
npm start
```

### 3. 数据库
初始化存储方案，包括关系型与图数据库：
```bash
cd database
# 执行数据库脚本，如：SQLite 或 Neo4j 脚本
```
---

**注意：项目各部分可分别调试与部署，确认模块无误后再集成运行。**