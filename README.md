# SalonFlow — 面向美发门店的多 Agent 经营服务智能体

针对社区美发小店客流管理、预约咨询、会员维护、物料库存、技师排班、工单记录繁杂的痛点，
搭建多智能体协同系统，结合 RAG 门店知识库与工具调用能力，实现智能预约、客诉接待、库存预警、
排班辅助、营销文案生成、台账自动汇总，配套管理后台，支持容器化部署。

## 技术栈

| 层 | 技术 |
|---|---|
| 智能体编排 | LangGraph（状态机、自主任务规划、多轮流转） |
| LLM 框架 | LangChain + DeepSeek API |
| 后端 | FastAPI（异步、SSE 流式、APIRouter、依赖注入、全局异常） |
| 前端 | Vue3 + Vite + Element Plus |
| 业务数据库 | MySQL |
| 向量数据库 | Qdrant（RAG 知识库） |
| 缓存 | Redis（可选，会话缓存 / 预约防冲突锁） |
| Embedding | 云 bge-m3 API |
| 部署 | Docker Compose |

## 目录结构

```
SalonFlow/
├── backend/            # FastAPI 后端
│   └── app/
│       ├── main.py     # 入口：统一响应 + 全局异常 + 启动建表/种子账号
│       ├── core/       # 配置 / JWT / 数据库 / 响应封装
│       ├── models/     # SQLAlchemy ORM 模型
│       ├── schemas/    # Pydantic 模型
│       └── api/        # 路由层（v1）
├── frontend/           # Vue3 前端（Dockerfile + nginx.conf）
└── docker-compose.yml  # MySQL + Qdrant + Redis + 后端 + 前端
```

## 快速启动

### 0. Docker 一键部署（推荐）

一次性构建并启动整套服务（MySQL / Qdrant / Redis / 后端 / 前端）：

```bash
docker compose up -d --build
```

- 前端：http://localhost:8080 （默认账号 `admin / admin123`）
- 后端接口文档：http://localhost:8080/api/docs
- 健康检查：http://localhost:8080/api/health

生产环境建议通过环境变量注入密钥（不写入镜像）：

```bash
SECRET_KEY=xxx DEEPSEEK_API_KEY=sk-xxx EMBEDDING_API_KEY=xxx docker compose up -d --build
```

> 说明：容器内 MySQL 以主机名 `mysql`、端口 `3306` 访问（宿主仍映射 `3307` 供本地开发）；Redis 当前预留、未接入业务。

### 1. 本地开发：启动基础设施（MySQL / Qdrant / Redis）

```bash
docker compose up -d
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # 按需修改配置
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 ，默认账号 `admin / admin123`。

- 后端接口文档：http://localhost:8000/api/docs
- 健康检查：http://localhost:8000/api/health

## 分阶段实施规划

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 项目脚手架（目录 / 统一响应 / 全局异常 / Docker） | ✅ 完成 |
| 1 | 登录与权限（JWT、三角色） | ✅ 完成 |
| 2 | 业务数据模块（会员 / 技师 / 库存 / 预约 CRUD） | ✅ 完成 |
| 3 | Agent 核心编排（LangGraph + 4 工具 + SSE 聊天） | ✅ 完成 |
| 4 | 右下角 Agent 悬浮窗（流式） | ✅ 完成 |
| 5 | RAG 知识库（Qdrant） | ✅ 完成 |
| 6 | 双层记忆（session + chat_history） | ✅ 完成 |
| 7 | 报表与预警（Excel 导出、营收/订单） | ✅ 完成 |
| 8 | 部署打磨（Docker 一键部署） | ✅ 完成 |
非第一次启动后端
cd d:\SalonFlow\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
前端
cd d:\SalonFlow\frontend
npm run dev