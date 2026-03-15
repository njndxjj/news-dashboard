# 后端模块说明

## 新增知识图谱 API 接口

### 功能
- **获取知识图谱节点**:
  - 提供 `/api/graph` 接口，返回知识图谱的节点数据。

### 配置
1. 确保 Neo4j 数据库已启动，并正确设置账户密码。
2. 调整代码中 Neo4j 的 `uri`, `user`, `password` 参数。

### 测试方法
1. 启动 Flask API:
   ```bash
   python app_knowledge_graph.py
   ```
2. 访问接口进行验证:
   - `http://localhost:5000/api/graph`

---