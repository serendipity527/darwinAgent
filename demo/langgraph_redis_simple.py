#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LangGraph + Redis 最简记忆对话实现
使用Redis存储会话数据，支持持久化和分布式部署
"""

from typing import Annotated, List
from typing_extensions import TypedDict
import redis

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 尝试导入Redis checkpointer
try:
    from langgraph_checkpoint_redis import RedisSaver
    print("✅ 使用 langgraph-checkpoint-redis")
except ImportError:
    try:
        from langgraph.checkpoint.redis import RedisSaver
        print("✅ 使用内置 Redis checkpointer")
    except ImportError:
        print("❌ Redis checkpointer 不可用")
        print("请安装: pip install langgraph-checkpoint-redis redis")
        RedisSaver = None

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import OllamaLLM

print("🚀 LangGraph + Redis 最简记忆对话")
print("=" * 40)

# ===================== Redis配置 =====================

# Redis连接配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # 如果有密码请设置
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# ===================== 状态定义 =====================

class ChatState(TypedDict):
    """对话状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]

# ===================== 聊天节点 =====================

def chat_node(state: ChatState):
    """
    聊天节点 - 处理用户消息并生成AI回复
    
    Args:
        state: 当前对话状态
        
    Returns:
        包含AI回复的状态更新
    """
    # 创建LLM实例
    llm = OllamaLLM(
        base_url="http://localhost:11434",
        model="gemma3:4b",
        temperature=0.7
    )
    
    # 系统消息
    system_message = SystemMessage(
        content="你是一个友好的AI助手，能记住对话历史。数据存储在Redis中，支持持久化。"
    )
    
    # 准备消息列表
    messages = [system_message] + state["messages"]
    
    # 调用LLM生成回复
    response = llm.invoke(messages)
    
    # 返回AI消息
    return {"messages": [AIMessage(content=response)]}

# ===================== 创建Redis聊天应用 =====================

def create_redis_chat_app():
    """
    创建使用Redis存储的LangGraph聊天应用
    
    Returns:
        编译后的聊天应用
    """
    if RedisSaver is None:
        print("❌ Redis checkpointer 不可用，请安装依赖")
        return None

    try:
        # 创建Redis连接
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        print("✅ Redis连接成功")

        # 创建Redis检查点保存器
        checkpointer = RedisSaver(redis_client)
        
        # 创建状态图
        graph = StateGraph(ChatState)
        
        # 添加节点和边
        graph.add_node("chat", chat_node)
        graph.add_edge(START, "chat")
        graph.add_edge("chat", END)
        
        # 编译应用
        app = graph.compile(checkpointer=checkpointer)
        
        print("✅ Redis聊天应用创建成功")
        return app
        
    except redis.ConnectionError:
        print("❌ Redis连接失败")
        print("请确保Redis服务正在运行:")
        print("- 安装Redis: https://redis.io/download")
        print("- 启动服务: redis-server")
        print("- 测试连接: redis-cli ping")
        return None
    except ImportError:
        print("❌ 缺少依赖包")
        print("请安装: pip install langgraph-checkpoint-redis redis")
        return None
    except Exception as e:
        print(f"❌ 创建应用失败: {e}")
        return None

# ===================== 聊天函数 =====================

def chat(app, message: str, session_id: str = "default") -> str:
    """
    发送消息并获取AI回复
    
    Args:
        app: LangGraph应用实例
        message: 用户消息
        session_id: 会话ID，用于区分不同用户
        
    Returns:
        AI的回复内容
    """
    if app is None:
        return "❌ 聊天应用未初始化"
    
    try:
        # 配置会话
        config = {"configurable": {"thread_id": session_id}}
        
        # 调用应用
        result = app.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        # 返回AI回复
        return result["messages"][-1].content
        
    except Exception as e:
        return f"❌ 聊天失败: {e}"

# ===================== 会话管理函数 =====================

def get_session_info(app, session_id: str = "default"):
    """
    获取会话信息
    
    Args:
        app: LangGraph应用实例
        session_id: 会话ID
        
    Returns:
        会话信息字典
    """
    if app is None:
        return {"error": "应用未初始化"}
    
    try:
        config = {"configurable": {"thread_id": session_id}}
        state = app.get_state(config)
        
        messages = state.values.get("messages", [])
        
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "last_update": state.created_at if hasattr(state, 'created_at') else "未知",
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                }
                for msg in messages[-5:]  # 显示最近5条消息
            ]
        }
    except Exception as e:
        return {"error": f"获取会话信息失败: {e}"}

# ===================== 主程序 =====================

def main():
    """主程序"""
    # 创建Redis聊天应用
    app = create_redis_chat_app()
    
    if app is None:
        print("❌ 应用初始化失败，程序退出")
        return
    
    # 测试对话
    print("\n🤖 Redis存储聊天测试:")
    print("=" * 40)
    
    # 第一轮对话
    response1 = chat(app, "你好，我是王五，职业是设计师", "test_session")
    print(f"👤 用户: 你好，我是王五，职业是设计师")
    print(f"🤖 AI: {response1}\n")
    
    # 第二轮对话 - 测试记忆
    response2 = chat(app, "你还记得我的姓名和职业吗？", "test_session")
    print(f"👤 用户: 你还记得我的姓名和职业吗？")
    print(f"🤖 AI: {response2}\n")
    
    # 第三轮对话 - 测试持久化
    response3 = chat(app, "我喜欢什么颜色？", "test_session")
    print(f"👤 用户: 我喜欢什么颜色？")
    print(f"🤖 AI: {response3}\n")
    
    response4 = chat(app, "我喜欢蓝色", "test_session")
    print(f"👤 用户: 我喜欢蓝色")
    print(f"🤖 AI: {response4}\n")
    
    # 获取会话信息
    session_info = get_session_info(app, "test_session")
    print("📊 会话信息:")
    print(f"- 会话ID: {session_info.get('session_id')}")
    print(f"- 消息数量: {session_info.get('message_count')}")
    print(f"- 最近消息: {len(session_info.get('messages', []))} 条")
    
    print("\n✅ Redis存储测试完成！")
    print("💡 特点:")
    print("- 数据持久化存储在Redis中")
    print("- 支持多用户会话隔离")
    print("- 程序重启后数据不丢失")
    print("- 支持分布式部署")

if __name__ == "__main__":
    main()
