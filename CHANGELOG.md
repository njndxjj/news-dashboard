# 更新日志

所有重要的项目变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 功能更新
- 初始版本发布
- Docker 一键部署支持
- 自动化更新脚本

---

## 版本说明

### 更新方式

**自动更新（推荐）**：
```bash
./update.sh
# 选择选项 1: 更新到最新版本
```

**手动更新**：
```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 回滚

如果更新后出现问题：
```bash
./update.sh
# 选择选项 2: 回滚到上一个版本
```
