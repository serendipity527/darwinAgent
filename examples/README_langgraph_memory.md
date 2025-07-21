# LangGraph 记忆对话实现指南

本目录包含了使用 LangGraph 实现记忆对话系统的完整示例，从基础实现到生产级API服务。

## 文件结构

```
examples/
├── langgraph_memory_example.py      # 基础LangGraph记忆对话示例
├── async_langgraph_memory.py        # 异步LangGraph记忆对话示例
├── fastapi_langgraph_memory.py      # FastAPI + LangGraph API服务
├── test_api_client.py               # API客户端测试工具
└── README_langgraph_memory.md       # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
# 基础依赖
pip install langgraph langchain-ollama langchain-core

# API服务依赖
pip install fastapi uvicorn websockets aiohttp

# 可选：持久化存储
pip install langgraph[sqlite]  # SQLite支持
pip install langgraph[postgres]  # PostgreSQL支持
```

### 2. 启动Ollama服务

```bash
# 启动Ollama
ollama serve

# 下载模型
ollama pull gemma:3b
```

### 3. 运行示例

#### 基础示例
```bash
python examples/langgraph_memory_example.py
```

#### 异步示例
```bash
python examples/async_langgraph_memory.py
```

#### API服务
```bash
# 启动API服务
python examples/fastapi_langgraph_memory.py

# 在另一个终端测试API
python examples/test_api_client.py
```

## 核心概念

### 1. 状态管理

LangGraph 使用 TypedDict 定义状态结构：

```python
from typing_extensions import TypedDict
from typing import Annotated, List
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_info: Dict[str, Any]  # 可选：用户信息
    summary: str  # 可选：对话摘要
```

### 2. 检查点机制

检查点用于保存和恢复对话状态：

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 内存存储（开发测试）
memory = MemorySaver()

# SQLite持久化（生产环境）
memory = SqliteSaver.from_conn_string("chat_memory.db")
```

### 3. 图结构

基于图的工作流设计：

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("chatbot", chatbot_node)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

app = graph.compile(checkpointer=memory)
```

## 功能特性

### ✅ 基础功能
- [x] 自动消息历史管理
- [x] 多用户会话隔离
- [x] 状态持久化
- [x] 错误恢复

### ✅ 高级功能
- [x] 消息修剪和摘要
- [x] 用户信息提取
- [x] 异步处理
- [x] 批量处理
- [x] 并发支持

### ✅ API功能
- [x] RESTful API接口
- [x] WebSocket实时通信
- [x] 健康检查
- [x] 性能监控

## 使用示例

### 基础聊天

```python
from examples.langgraph_memory_example import LangGraphChatApp

# 创建聊天应用
app = LangGraphChatApp(use_advanced=True)

# 发送消息
response = app.chat("你好，我叫Alice", "user_session_1")
print(response)

# 继续对话
response = app.chat("你还记得我的名字吗？", "user_session_1")
print(response)
```

### 异步聊天

```python
from examples.async_langgraph_memory import AsyncLangGraphChatApp

async def chat_example():
    app = AsyncLangGraphChatApp()
    
    result = await app.chat("你好，我是Bob", "async_session")
    print(result['response'])

asyncio.run(chat_example())
```

### API调用

```python
import aiohttp

async def api_chat():
    async with aiohttp.ClientSession() as session:
        data = {
            "message": "你好，我是Charlie",
            "session_id": "api_session"
        }
        
        async with session.post("http://localhost:8000/chat", json=data) as response:
            result = await response.json()
            print(result['response'])

asyncio.run(api_chat())
```

## 配置选项

### 模型配置

```python
# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma:3b"  # 或其他模型

# OpenAI配置（可选）
OPENAI_API_KEY = "your-api-key"
OPENAI_MODEL = "gpt-3.5-turbo"
```

### 记忆配置

```python
# 消息修剪阈值
MAX_MESSAGES = 10

# 摘要生成阈值
SUMMARY_THRESHOLD = 8

# 会话超时（秒）
SESSION_TIMEOUT = 3600
```

## 性能优化

### 1. 异步处理
- 使用 `asyncio` 进行并发处理
- 支持批量消息处理
- WebSocket实时通信

### 2. 内存管理
- 自动消息修剪
- 对话摘要生成
- 状态压缩

### 3. 缓存策略
- 用户信息缓存
- 模型响应缓存
- 会话状态缓存

## 部署指南

### 1. 开发环境

```bash
# 直接运行
python examples/fastapi_langgraph_memory.py
```

### 2. 生产环境

```bash
# 使用Gunicorn
pip install gunicorn
gunicorn examples.fastapi_langgraph_memory:app -w 4 -k uvicorn.workers.UvicornWorker

# 使用Docker
docker build -t langgraph-chat-api .
docker run -p 8000:8000 langgraph-chat-api
```

### 3. 环境变量

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="gemma:3b"
export DATABASE_URL="sqlite:///chat_memory.db"
```

## 监控和日志

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

### 2. 性能监控

```python
# 处理时间监控
processing_time = result.get('processing_time', 0)

# 会话统计
session_stats = app.get_session_stats(session_id)
```

### 3. 错误处理

```python
try:
    response = await app.chat(message, session_id)
except Exception as e:
    logger.error(f"聊天处理失败: {e}")
    # 错误恢复逻辑
```

## 扩展功能

### 1. 自定义节点

```python
def custom_node(state: State):
    # 自定义处理逻辑
    return {"messages": [...]}

graph.add_node("custom", custom_node)
```

### 2. 条件路由

```python
def should_summarize(state: State):
    return len(state["messages"]) > 10

graph.add_conditional_edges(
    "chatbot",
    should_summarize,
    {True: "summarize", False: END}
)
```

### 3. 工具集成

```python
from langgraph.prebuilt import create_react_agent

# 集成工具
tools = [search_tool, calculator_tool]
agent = create_react_agent(llm, tools, checkpointer=memory)
```

## 故障排除

### 常见问题

1. **Ollama连接失败**
   ```bash
   # 检查Ollama服务
   ollama list
   ollama serve
   ```

2. **内存不足**
   ```python
   # 减少消息历史长度
   MAX_MESSAGES = 5
   ```

3. **响应慢**
   ```python
   # 使用更小的模型
   OLLAMA_MODEL = "gemma:2b"
   ```

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看状态
state = app.get_state(config)
print(state.values)
```

## 最佳实践

1. **状态设计**: 保持状态结构简单清晰
2. **错误处理**: 实现完善的错误恢复机制
3. **性能监控**: 监控处理时间和资源使用
4. **安全考虑**: 验证用户输入，防止注入攻击
5. **扩展性**: 设计可扩展的节点和工作流

## 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangChain 文档](https://python.langchain.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Ollama 文档](https://ollama.ai/docs)

## 贡献

欢迎提交Issue和Pull Request来改进这些示例！
