# LangGraph 记忆对话实现指南

## 概述

LangGraph 是 LangChain 0.3+ 推荐的记忆管理方式，相比传统的 Memory 类，它提供了更强大、更灵活的状态管理能力。本指南将详细介绍如何使用 LangGraph 实现记忆对话系统。

## 核心概念

### 1. 状态管理 (State Management)
LangGraph 使用 TypedDict 定义状态结构，通过 `add_messages` 函数自动管理消息历史。

### 2. 检查点 (Checkpointer)
检查点机制允许保存和恢复对话状态，支持多用户、多会话管理。

### 3. 图结构 (Graph Structure)
基于图的工作流设计，支持复杂的对话逻辑和状态转换。

## 基础实现

### 1. 安装依赖

```bash
pip install langgraph langchain-ollama langchain-core
```

### 2. 基础记忆对话系统

```python
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import OllamaLLM

# 定义状态
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# 创建LLM
llm = OllamaLLM(
    base_url="http://localhost:11434",
    model="gemma:3b",
    temperature=0.7
)

# 聊天机器人节点
def chatbot_node(state: State):
    """处理用户消息并生成回复"""
    # 添加系统消息
    system_message = SystemMessage(content="""你是一个友好的AI助手。
你能记住对话历史，并基于之前的对话内容进行回复。
请保持友好、有帮助的态度。""")
    
    # 准备消息列表
    messages = [system_message] + state["messages"]
    
    # 调用LLM生成回复
    response = llm.invoke(messages)
    
    # 返回AI消息
    return {"messages": [AIMessage(content=response)]}

# 创建图
def create_chat_graph():
    """创建聊天图"""
    graph = StateGraph(State)
    
    # 添加节点
    graph.add_node("chatbot", chatbot_node)
    
    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 添加记忆检查点
    memory = MemorySaver()
    
    # 编译图
    return graph.compile(checkpointer=memory)

# 创建聊天应用
chat_app = create_chat_graph()

# 使用示例
def chat_example():
    # 配置会话
    config = {"configurable": {"thread_id": "user_session_1"}}
    
    # 发送消息
    result = chat_app.invoke(
        {"messages": [HumanMessage(content="你好，我叫Alice")]},
        config=config
    )
    
    print(f"AI: {result['messages'][-1].content}")
    
    # 继续对话
    result = chat_app.invoke(
        {"messages": [HumanMessage(content="你还记得我的名字吗？")]},
        config=config
    )
    
    print(f"AI: {result['messages'][-1].content}")
```

## 高级功能

### 1. 消息修剪和摘要

```python
from langchain_core.messages import trim_messages

class AdvancedState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    summary: str  # 对话摘要

def summarize_conversation(messages: List[BaseMessage], llm) -> str:
    """总结对话历史"""
    if len(messages) < 4:
        return ""
    
    summary_prompt = f"""请简洁地总结以下对话的要点：

{chr(10).join([f"{type(msg).__name__}: {msg.content}" for msg in messages[:-2]])}

摘要:"""
    
    try:
        return llm.invoke(summary_prompt)
    except:
        return "对话摘要生成失败"

def advanced_chatbot_node(state: AdvancedState):
    """支持消息修剪和摘要的聊天节点"""
    messages = state["messages"]
    summary = state.get("summary", "")
    
    # 如果消息太多，进行修剪
    if len(messages) > 10:
        # 生成摘要
        if not summary:
            summary = summarize_conversation(messages[:-6], llm)
        
        # 修剪消息，只保留最近的消息
        trimmed_messages = messages[-6:]
        
        # 创建包含摘要的系统消息
        system_content = f"""你是一个友好的AI助手。

对话摘要: {summary}

请基于对话摘要和最近的对话历史进行回复。"""
        
        system_message = SystemMessage(content=system_content)
        final_messages = [system_message] + trimmed_messages
        
        return {
            "messages": [AIMessage(content=llm.invoke(final_messages))],
            "summary": summary
        }
    else:
        # 正常处理
        system_message = SystemMessage(content="你是一个友好的AI助手，能记住对话历史。")
        final_messages = [system_message] + messages
        
        return {
            "messages": [AIMessage(content=llm.invoke(final_messages))],
            "summary": summary
        }
```

### 2. 多用户会话管理

```python
def multi_user_example():
    """多用户会话示例"""
    
    # 用户1的会话
    user1_config = {"configurable": {"thread_id": "user_alice"}}
    user2_config = {"configurable": {"thread_id": "user_bob"}}
    
    # 用户1的对话
    result1 = chat_app.invoke(
        {"messages": [HumanMessage(content="你好，我是Alice，我喜欢画画")]},
        config=user1_config
    )
    print(f"Alice: 你好，我是Alice，我喜欢画画")
    print(f"AI: {result1['messages'][-1].content}")
    
    # 用户2的对话
    result2 = chat_app.invoke(
        {"messages": [HumanMessage(content="嗨，我是Bob，我是程序员")]},
        config=user2_config
    )
    print(f"Bob: 嗨，我是Bob，我是程序员")
    print(f"AI: {result2['messages'][-1].content}")
    
    # 继续用户1的对话
    result3 = chat_app.invoke(
        {"messages": [HumanMessage(content="你还记得我的爱好吗？")]},
        config=user1_config
    )
    print(f"Alice: 你还记得我的爱好吗？")
    print(f"AI: {result3['messages'][-1].content}")
```

## 状态持久化

### 1. 使用不同的检查点存储

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver

# SQLite 持久化
def create_persistent_chat_graph():
    """创建持久化聊天图"""
    graph = StateGraph(State)
    graph.add_node("chatbot", chatbot_node)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 使用SQLite持久化
    memory = SqliteSaver.from_conn_string("chat_memory.db")
    
    return graph.compile(checkpointer=memory)

# PostgreSQL 持久化
def create_postgres_chat_graph():
    """创建PostgreSQL持久化聊天图"""
    graph = StateGraph(State)
    graph.add_node("chatbot", chatbot_node)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 使用PostgreSQL持久化
    memory = PostgresSaver.from_conn_string("postgresql://user:pass@localhost/db")
    
    return graph.compile(checkpointer=memory)
```

### 2. 状态查询和管理

```python
def manage_conversation_state():
    """管理对话状态"""
    config = {"configurable": {"thread_id": "user_session_1"}}
    
    # 获取当前状态
    state = chat_app.get_state(config)
    print(f"当前消息数: {len(state.values['messages'])}")
    
    # 查看历史消息
    for msg in state.values["messages"]:
        role = "用户" if isinstance(msg, HumanMessage) else "AI"
        print(f"{role}: {msg.content}")
    
    # 获取状态历史
    history = chat_app.get_state_history(config)
    for checkpoint in history:
        print(f"检查点: {checkpoint.config}")
```

## 最佳实践

### 1. 错误处理

```python
def robust_chatbot_node(state: State):
    """带错误处理的聊天节点"""
    try:
        system_message = SystemMessage(content="你是一个友好的AI助手。")
        messages = [system_message] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [AIMessage(content=response)]}
    except Exception as e:
        error_message = f"抱歉，我遇到了一个错误: {str(e)}"
        return {"messages": [AIMessage(content=error_message)]}
```

### 2. 性能优化

```python
def optimized_chatbot_node(state: State):
    """优化的聊天节点"""
    messages = state["messages"]
    
    # 限制上下文长度
    max_context_messages = 20
    if len(messages) > max_context_messages:
        messages = messages[-max_context_messages:]
    
    system_message = SystemMessage(content="你是一个友好的AI助手。")
    final_messages = [system_message] + messages
    
    response = llm.invoke(final_messages)
    return {"messages": [AIMessage(content=response)]}
```

## 与传统Memory的对比

| 特性 | 传统Memory类 | LangGraph记忆 |
|------|-------------|---------------|
| 多用户支持 | ❌ 需要手动实现 | ✅ 内置支持 |
| 多会话管理 | ❌ 复杂 | ✅ 简单配置 |
| 状态持久化 | ❌ 有限 | ✅ 完整支持 |
| 错误恢复 | ❌ 困难 | ✅ 内置支持 |
| 复杂状态管理 | ❌ 不支持 | ✅ 完全支持 |
| 工具调用兼容 | ❌ 有问题 | ✅ 完美兼容 |

## 总结

LangGraph 提供了现代化的记忆管理解决方案，具有以下优势：

1. **架构优势**: 基于图的状态管理，支持复杂工作流
2. **多用户支持**: 天然支持多用户、多会话
3. **状态持久化**: 完整的状态保存和恢复
4. **开发体验**: 更直观的API设计，更好的调试支持
5. **性能和可靠性**: 更好的内存管理，生产环境就绪

对于新项目，强烈推荐直接使用 LangGraph 来实现记忆对话功能。
