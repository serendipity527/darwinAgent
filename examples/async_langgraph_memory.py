#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
异步 LangGraph 记忆对话系统
展示如何使用异步方式实现高性能的记忆对话
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
from typing_extensions import TypedDict

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import OllamaLLM

print("异步 LangGraph 记忆对话系统")
print("=" * 40)

# ===================== 配置部分 =====================

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma:3b"

def create_llm():
    """创建LLM实例"""
    return OllamaLLM(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0.7
    )

llm = create_llm()

# ===================== 异步状态定义 =====================

class AsyncState(TypedDict):
    """异步状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_info: Dict[str, Any]
    processing_time: float

# ===================== 异步节点函数 =====================

async def async_chatbot_node(state: AsyncState):
    """异步聊天机器人节点"""
    start_time = asyncio.get_event_loop().time()
    
    # 提取用户信息
    user_info = await extract_user_info_async(state["messages"])
    
    # 创建系统消息
    user_context = ""
    if user_info:
        user_context = f"用户信息: {user_info}\n\n"
    
    system_content = f"""你是一个友好的AI助手，能记住对话历史。

{user_context}请基于用户信息和对话历史进行个性化回复。"""
    
    system_message = SystemMessage(content=system_content)
    messages = [system_message] + state["messages"]
    
    # 异步调用LLM
    response = await asyncio.to_thread(llm.invoke, messages)
    
    processing_time = asyncio.get_event_loop().time() - start_time
    
    return {
        "messages": [AIMessage(content=response)],
        "user_info": user_info,
        "processing_time": processing_time
    }

async def extract_user_info_async(messages: List[BaseMessage]) -> Dict[str, Any]:
    """异步提取用户信息"""
    user_info = {}
    
    # 模拟异步处理
    await asyncio.sleep(0.01)
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content.lower()
            
            # 提取姓名
            if "我叫" in content or "我是" in content:
                words = content.split()
                for i, word in enumerate(words):
                    if word in ["我叫", "我是"] and i + 1 < len(words):
                        user_info["name"] = words[i + 1].replace("，", "").replace(",", "")
                        break
            
            # 提取职业
            jobs = ["程序员", "工程师", "老师", "医生", "学生", "设计师", "销售"]
            for job in jobs:
                if job in content:
                    user_info["job"] = job
                    break
            
            # 提取爱好
            if "喜欢" in content:
                user_info["interests"] = content
    
    return user_info

# ===================== 异步图创建 =====================

def create_async_chat_graph():
    """创建异步聊天图"""
    graph = StateGraph(AsyncState)
    
    # 添加节点
    graph.add_node("chatbot", async_chatbot_node)
    
    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 添加内存检查点
    memory = MemorySaver()
    
    # 编译图
    return graph.compile(checkpointer=memory)

# ===================== 异步聊天应用类 =====================

class AsyncLangGraphChatApp:
    """异步LangGraph聊天应用"""
    
    def __init__(self):
        self.app = create_async_chat_graph()
        self.session_stats = {}
    
    async def chat(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """异步发送消息并获取回复"""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            result = await self.app.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            
            total_time = asyncio.get_event_loop().time() - start_time
            
            # 更新会话统计
            if session_id not in self.session_stats:
                self.session_stats[session_id] = {
                    "message_count": 0,
                    "total_time": 0,
                    "avg_time": 0
                }
            
            stats = self.session_stats[session_id]
            stats["message_count"] += 1
            stats["total_time"] += total_time
            stats["avg_time"] = stats["total_time"] / stats["message_count"]
            
            return {
                "response": result["messages"][-1].content,
                "user_info": result.get("user_info", {}),
                "processing_time": result.get("processing_time", 0),
                "total_time": total_time,
                "session_stats": stats
            }
            
        except Exception as e:
            return {
                "response": f"抱歉，我遇到了一个错误: {str(e)}",
                "error": True
            }
    
    async def get_conversation_history(self, session_id: str = "default") -> List[BaseMessage]:
        """异步获取对话历史"""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            state = await self.app.aget_state(config)
            return state.values.get("messages", [])
        except Exception as e:
            print(f"获取历史失败: {e}")
            return []
    
    async def batch_chat(self, messages: List[str], session_id: str = "default") -> List[Dict[str, Any]]:
        """批量处理消息"""
        tasks = []
        for i, message in enumerate(messages):
            # 为每个消息创建唯一的临时session_id
            temp_session_id = f"{session_id}_batch_{i}"
            tasks.append(self.chat(message, temp_session_id))
        
        results = await asyncio.gather(*tasks)
        return results
    
    def get_session_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """获取会话统计信息"""
        return self.session_stats.get(session_id, {})

# ===================== 异步演示函数 =====================

async def demo_async_chat():
    """演示异步聊天功能"""
    print("\n=== 异步聊天演示 ===")
    
    app = AsyncLangGraphChatApp()
    session_id = "async_demo"
    
    conversations = [
        "你好，我叫Charlie，是一名设计师",
        "我在一家广告公司工作",
        "我喜欢创意设计和用户体验",
        "你还记得我的名字和职业吗？"
    ]
    
    for i, message in enumerate(conversations, 1):
        result = await app.chat(message, session_id)
        
        print(f"\n第{i}轮:")
        print(f"用户: {message}")
        print(f"AI: {result['response']}")
        print(f"处理时间: {result.get('processing_time', 0):.3f}s")
        print(f"总时间: {result.get('total_time', 0):.3f}s")
        
        if result.get('user_info'):
            print(f"用户信息: {result['user_info']}")

async def demo_concurrent_users():
    """演示并发用户处理"""
    print("\n=== 并发用户演示 ===")
    
    app = AsyncLangGraphChatApp()
    
    # 模拟多个用户同时发送消息
    user_messages = [
        ("user_1", "你好，我是Alice，我是程序员"),
        ("user_2", "嗨，我是Bob，我是老师"),
        ("user_3", "你好，我是Carol，我是医生"),
        ("user_4", "hi，我是David，我是学生"),
        ("user_5", "你好，我是Eve，我是销售")
    ]
    
    # 并发处理所有用户消息
    start_time = asyncio.get_event_loop().time()
    
    tasks = [app.chat(message, session_id) for session_id, message in user_messages]
    results = await asyncio.gather(*tasks)
    
    total_time = asyncio.get_event_loop().time() - start_time
    
    print(f"并发处理 {len(user_messages)} 个用户消息")
    print(f"总耗时: {total_time:.3f}s")
    print(f"平均每个用户: {total_time/len(user_messages):.3f}s")
    
    for i, (result, (session_id, message)) in enumerate(zip(results, user_messages)):
        print(f"\n用户 {session_id}:")
        print(f"消息: {message}")
        print(f"回复: {result['response']}")
        print(f"处理时间: {result.get('processing_time', 0):.3f}s")

async def demo_batch_processing():
    """演示批量处理"""
    print("\n=== 批量处理演示 ===")
    
    app = AsyncLangGraphChatApp()
    
    messages = [
        "你好，我叫Frank",
        "我是一名工程师",
        "我喜欢编程和阅读",
        "我在北京工作",
        "你能总结一下我的信息吗？"
    ]
    
    print("批量处理消息...")
    start_time = asyncio.get_event_loop().time()
    
    results = await app.batch_chat(messages, "batch_demo")
    
    total_time = asyncio.get_event_loop().time() - start_time
    
    print(f"批量处理完成，总耗时: {total_time:.3f}s")
    
    for i, (message, result) in enumerate(zip(messages, results)):
        print(f"\n消息 {i+1}: {message}")
        print(f"回复: {result['response']}")

async def demo_streaming_chat():
    """演示流式聊天（模拟）"""
    print("\n=== 流式聊天演示 ===")
    
    app = AsyncLangGraphChatApp()
    session_id = "streaming_demo"
    
    message = "请详细介绍一下人工智能的发展历史"
    
    print(f"用户: {message}")
    print("AI: ", end="", flush=True)
    
    # 模拟流式输出
    result = await app.chat(message, session_id)
    response = result['response']
    
    # 逐字输出模拟流式效果
    for char in response:
        print(char, end="", flush=True)
        await asyncio.sleep(0.02)  # 模拟打字效果
    
    print(f"\n\n处理时间: {result.get('processing_time', 0):.3f}s")

async def interactive_async_chat():
    """异步交互式聊天"""
    print("\n=== 异步交互式聊天 ===")
    print("输入 'quit' 退出，输入 'stats' 查看统计信息")
    
    app = AsyncLangGraphChatApp()
    session_id = input("请输入会话ID (默认: default): ").strip() or "default"
    
    print(f"\n开始异步聊天 (会话: {session_id})")
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            elif user_input.lower() == 'stats':
                stats = app.get_session_stats(session_id)
                print(f"会话统计: {stats}")
                continue
            elif not user_input:
                continue
            
            # 显示处理中状态
            print("AI正在思考...", end="", flush=True)
            
            result = await app.chat(user_input, session_id)
            
            # 清除"思考中"提示
            print("\r" + " " * 20 + "\r", end="")
            
            print(f"AI: {result['response']}")
            print(f"(处理时间: {result.get('processing_time', 0):.3f}s)")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"出错了: {e}")

# ===================== 性能测试 =====================

async def performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    app = AsyncLangGraphChatApp()
    
    # 测试不同并发级别
    concurrency_levels = [1, 5, 10, 20]
    test_message = "你好，请介绍一下你自己"
    
    for concurrency in concurrency_levels:
        print(f"\n测试并发级别: {concurrency}")
        
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(concurrency):
            session_id = f"perf_test_{concurrency}_{i}"
            tasks.append(app.chat(test_message, session_id))
        
        results = await asyncio.gather(*tasks)
        
        total_time = asyncio.get_event_loop().time() - start_time
        avg_time = total_time / concurrency
        
        print(f"总耗时: {total_time:.3f}s")
        print(f"平均耗时: {avg_time:.3f}s")
        print(f"QPS: {concurrency/total_time:.2f}")

# ===================== 主函数 =====================

async def main():
    """异步主函数"""
    print("异步 LangGraph 记忆对话系统")
    print("=" * 40)
    
    try:
        # 测试LLM连接
        test_response = await asyncio.to_thread(llm.invoke, "Hello")
        print("✓ Ollama 连接成功")
    except Exception as e:
        print(f"✗ Ollama 连接失败: {e}")
        return
    
    while True:
        print("\n请选择演示模式:")
        print("1. 异步聊天演示")
        print("2. 并发用户演示")
        print("3. 批量处理演示")
        print("4. 流式聊天演示")
        print("5. 异步交互式聊天")
        print("6. 性能测试")
        print("7. 退出")
        
        choice = input("\n请输入选择 (1-7): ").strip()
        
        if choice == "1":
            await demo_async_chat()
        elif choice == "2":
            await demo_concurrent_users()
        elif choice == "3":
            await demo_batch_processing()
        elif choice == "4":
            await demo_streaming_chat()
        elif choice == "5":
            await interactive_async_chat()
        elif choice == "6":
            await performance_test()
        elif choice == "7":
            print("再见！")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    asyncio.run(main())
