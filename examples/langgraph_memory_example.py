#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LangGraph 记忆对话完整实现示例
展示如何使用 LangGraph 构建具有记忆功能的对话系统
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
from typing_extensions import TypedDict

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM

print("LangGraph 记忆对话系统示例")
print("=" * 50)

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

# ===================== 1. 基础记忆对话系统 =====================

class BasicState(TypedDict):
    """基础状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]

def basic_chatbot_node(state: BasicState):
    """基础聊天机器人节点"""
    # 创建系统消息
    system_message = SystemMessage(content="""你是一个友好的AI助手。
你能记住对话历史，并基于之前的对话内容进行回复。
请保持友好、有帮助的态度。""")
    
    # 准备消息列表
    messages = [system_message] + state["messages"]
    
    # 调用LLM
    response = llm.invoke(messages)
    
    # 返回AI消息
    return {"messages": [AIMessage(content=response)]}

def create_basic_chat_graph():
    """创建基础聊天图"""
    graph = StateGraph(BasicState)
    
    # 添加节点
    graph.add_node("chatbot", basic_chatbot_node)
    
    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 添加内存检查点
    memory = MemorySaver()
    
    # 编译图
    return graph.compile(checkpointer=memory)

# ===================== 2. 高级记忆对话系统 =====================

class AdvancedState(TypedDict):
    """高级状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    summary: str  # 对话摘要
    user_info: Dict[str, Any]  # 用户信息

def summarize_conversation(messages: List[BaseMessage]) -> str:
    """总结对话历史"""
    if len(messages) < 4:
        return ""
    
    # 创建摘要提示
    summary_prompt = f"""请简洁地总结以下对话的要点，保留重要信息：

{chr(10).join([f"{type(msg).__name__}: {msg.content}" for msg in messages[:-2]])}

摘要:"""
    
    try:
        summary = llm.invoke(summary_prompt)
        return summary
    except Exception as e:
        return f"对话摘要生成失败: {str(e)}"

def extract_user_info(messages: List[BaseMessage]) -> Dict[str, Any]:
    """从对话中提取用户信息"""
    user_info = {}
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content.lower()
            
            # 提取姓名
            if "我叫" in content or "我是" in content:
                # 简单的姓名提取逻辑
                words = content.split()
                for i, word in enumerate(words):
                    if word in ["我叫", "我是"] and i + 1 < len(words):
                        user_info["name"] = words[i + 1].replace("，", "").replace(",", "")
                        break
            
            # 提取职业
            if any(job in content for job in ["程序员", "工程师", "老师", "医生", "学生"]):
                for job in ["程序员", "工程师", "老师", "医生", "学生"]:
                    if job in content:
                        user_info["job"] = job
                        break
            
            # 提取爱好
            if "喜欢" in content:
                user_info["interests"] = content
    
    return user_info

def advanced_chatbot_node(state: AdvancedState):
    """高级聊天机器人节点"""
    messages = state["messages"]
    summary = state.get("summary", "")
    user_info = state.get("user_info", {})
    
    # 更新用户信息
    new_user_info = extract_user_info(messages)
    user_info.update(new_user_info)
    
    # 如果消息太多，进行修剪和摘要
    if len(messages) > 10:
        # 生成摘要
        if not summary:
            summary = summarize_conversation(messages[:-6])
        else:
            # 更新摘要
            recent_summary = summarize_conversation(messages[-8:-2])
            summary = f"{summary}\n\n最近对话: {recent_summary}"
        
        # 修剪消息，只保留最近的消息
        trimmed_messages = messages[-6:]
        
        # 创建包含摘要和用户信息的系统消息
        user_context = ""
        if user_info:
            user_context = f"用户信息: {user_info}"
        
        system_content = f"""你是一个友好的AI助手。

{user_context}

对话摘要: {summary}

请基于用户信息、对话摘要和最近的对话历史进行个性化回复。"""
        
        system_message = SystemMessage(content=system_content)
        final_messages = [system_message] + trimmed_messages
        
        response = llm.invoke(final_messages)
        
        return {
            "messages": [AIMessage(content=response)],
            "summary": summary,
            "user_info": user_info
        }
    else:
        # 正常处理
        user_context = ""
        if user_info:
            user_context = f"用户信息: {user_info}\n\n"
        
        system_content = f"""你是一个友好的AI助手，能记住对话历史。

{user_context}请基于用户信息和对话历史进行个性化回复。"""
        
        system_message = SystemMessage(content=system_content)
        final_messages = [system_message] + messages
        
        response = llm.invoke(final_messages)
        
        return {
            "messages": [AIMessage(content=response)],
            "summary": summary,
            "user_info": user_info
        }

def create_advanced_chat_graph():
    """创建高级聊天图"""
    graph = StateGraph(AdvancedState)
    
    # 添加节点
    graph.add_node("chatbot", advanced_chatbot_node)
    
    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 添加内存检查点
    memory = MemorySaver()
    
    # 编译图
    return graph.compile(checkpointer=memory)

# ===================== 3. 持久化记忆对话系统 =====================

def create_persistent_chat_graph():
    """创建持久化聊天图"""
    graph = StateGraph(AdvancedState)
    
    # 添加节点
    graph.add_node("chatbot", advanced_chatbot_node)
    
    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 使用SQLite持久化
    memory = SqliteSaver.from_conn_string("chat_memory.db")
    
    # 编译图
    return graph.compile(checkpointer=memory)

# ===================== 4. 聊天应用类 =====================

class LangGraphChatApp:
    """LangGraph聊天应用封装类"""
    
    def __init__(self, use_persistent=False, use_advanced=True):
        self.use_persistent = use_persistent
        self.use_advanced = use_advanced
        
        if use_advanced:
            if use_persistent:
                self.app = create_persistent_chat_graph()
            else:
                self.app = create_advanced_chat_graph()
        else:
            self.app = create_basic_chat_graph()
    
    def chat(self, message: str, session_id: str = "default") -> str:
        """发送消息并获取回复"""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            result = self.app.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            return result["messages"][-1].content
        except Exception as e:
            return f"抱歉，我遇到了一个错误: {str(e)}"
    
    def get_conversation_history(self, session_id: str = "default") -> List[BaseMessage]:
        """获取对话历史"""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            state = self.app.get_state(config)
            return state.values.get("messages", [])
        except Exception as e:
            print(f"获取历史失败: {e}")
            return []
    
    def get_conversation_info(self, session_id: str = "default") -> Dict[str, Any]:
        """获取对话信息"""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            state = self.app.get_state(config)
            return {
                "message_count": len(state.values.get("messages", [])),
                "summary": state.values.get("summary", ""),
                "user_info": state.values.get("user_info", {}),
                "session_id": session_id
            }
        except Exception as e:
            print(f"获取信息失败: {e}")
            return {}
    
    def clear_conversation(self, session_id: str = "default"):
        """清空对话历史"""
        # 注意: LangGraph的检查点不支持直接清空，需要使用新的session_id
        print(f"要清空对话，请使用新的session_id")

# ===================== 5. 演示函数 =====================

def demo_basic_chat():
    """演示基础聊天功能"""
    print("\n=== 基础聊天演示 ===")
    
    app = LangGraphChatApp(use_advanced=False)
    session_id = "basic_demo"
    
    conversations = [
        "你好，我叫Alice，是一名数据科学家",
        "我在研究机器学习算法",
        "你还记得我的名字吗？",
        "我的职业是什么？"
    ]
    
    for i, message in enumerate(conversations, 1):
        response = app.chat(message, session_id)
        print(f"\n第{i}轮:")
        print(f"用户: {message}")
        print(f"AI: {response}")

def demo_advanced_chat():
    """演示高级聊天功能"""
    print("\n=== 高级聊天演示 ===")
    
    app = LangGraphChatApp(use_advanced=True)
    session_id = "advanced_demo"
    
    conversations = [
        "你好，我叫Bob，是一名软件工程师",
        "我在一家科技公司工作，主要做后端开发",
        "我喜欢Python和Go语言",
        "最近在学习Kubernetes和Docker",
        "我的团队有8个人",
        "我们正在开发一个微服务架构的项目",
        "这个项目预计需要6个月完成",
        "我们使用敏捷开发方法",
        "每两周一个迭代",
        "我负责用户认证模块",
        "还有API网关的设计",
        "你还记得我的名字吗？",
        "我在做什么项目？",
        "我负责哪些模块？"
    ]
    
    for i, message in enumerate(conversations, 1):
        response = app.chat(message, session_id)
        print(f"\n第{i}轮:")
        print(f"用户: {message}")
        print(f"AI: {response}")
        
        # 每5轮显示一次对话信息
        if i % 5 == 0:
            info = app.get_conversation_info(session_id)
            print(f"\n对话信息: {info}")

def demo_multi_user():
    """演示多用户功能"""
    print("\n=== 多用户演示 ===")
    
    app = LangGraphChatApp(use_advanced=True)
    
    # 用户1
    print("\n--- 用户Alice ---")
    response1 = app.chat("你好，我是Alice，我喜欢画画", "user_alice")
    print(f"Alice: 你好，我是Alice，我喜欢画画")
    print(f"AI: {response1}")
    
    # 用户2
    print("\n--- 用户Bob ---")
    response2 = app.chat("嗨，我是Bob，我是程序员", "user_bob")
    print(f"Bob: 嗨，我是Bob，我是程序员")
    print(f"AI: {response2}")
    
    # 继续用户1的对话
    print("\n--- 继续Alice的对话 ---")
    response3 = app.chat("你还记得我的爱好吗？", "user_alice")
    print(f"Alice: 你还记得我的爱好吗？")
    print(f"AI: {response3}")
    
    # 继续用户2的对话
    print("\n--- 继续Bob的对话 ---")
    response4 = app.chat("我的职业是什么？", "user_bob")
    print(f"Bob: 我的职业是什么？")
    print(f"AI: {response4}")

def interactive_chat():
    """交互式聊天"""
    print("\n=== 交互式聊天 ===")
    print("输入 'quit' 退出，输入 'info' 查看对话信息")
    
    app = LangGraphChatApp(use_advanced=True, use_persistent=True)
    session_id = input("请输入会话ID (默认: default): ").strip() or "default"
    
    print(f"\n开始与AI聊天 (会话: {session_id})")
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            elif user_input.lower() == 'info':
                info = app.get_conversation_info(session_id)
                print(f"对话信息: {info}")
                continue
            elif not user_input:
                continue
            
            response = app.chat(user_input, session_id)
            print(f"AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"出错了: {e}")

# ===================== 主函数 =====================

def main():
    """主函数"""
    print("LangGraph 记忆对话系统")
    print("=" * 40)
    
    try:
        # 测试LLM连接
        test_response = llm.invoke("Hello")
        print("✓ Ollama 连接成功")
    except Exception as e:
        print(f"✗ Ollama 连接失败: {e}")
        print("请确保 Ollama 正在运行: ollama serve")
        print("并安装模型: ollama pull gemma:3b")
        return
    
    while True:
        print("\n请选择演示模式:")
        print("1. 基础聊天演示")
        print("2. 高级聊天演示")
        print("3. 多用户演示")
        print("4. 交互式聊天")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            demo_basic_chat()
        elif choice == "2":
            demo_advanced_chat()
        elif choice == "3":
            demo_multi_user()
        elif choice == "4":
            interactive_chat()
        elif choice == "5":
            print("再见！")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()
