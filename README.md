# FastAPI LangChain LangGraph Agent 项目

这是一个使用 FastAPI 构建的 LangChain 和 LangGraph Agent 项目，提供了一个可扩展的框架来构建和部署基于大语言模型的智能代理系统。

## 特点

- 基于 FastAPI 的高性能 API 服务
- 使用 LangChain 构建灵活的处理链
- 使用 LangGraph 设计复杂的代理工作流
- 模块化设计，易于扩展和自定义
- Docker 支持，便于部署

## 安装

1. 克隆仓库

```bash
git clone <repository-url>
cd project
```

2. 创建并激活虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 设置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

## 使用方法

### 开发模式运行

```bash
uvicorn app.main:app --reload
```

### 使用 Docker 运行

```bash
docker-compose up -d
```

## 项目结构

项目采用模块化设计，详细的目录结构请参考 `project_struct.txt` 文件。

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

运行测试：

```bash
pytest
```

## 许可证

[MIT](LICENSE)
