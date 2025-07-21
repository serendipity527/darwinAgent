#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LCEL 对话记忆运行脚本
演示使用 LCEL 实现对话记忆的不同方法
"""

import os
import sys
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

# 配置
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma:3b"

def create_llm():
    """创建LLM实例"""
    return OllamaLLM(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0.7
    )

# ===================== 实现类 =====================

class ManualMemoryChain:
    """手动管理对话历史的链"""
    
    def __init__(self, llm):
        self.llm = llm
        self.history: List[BaseMessage] = []
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个友好的AI助手，能够记住对话历史。"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def invoke(self, user_input: str) -> str:
        response = self.chain.invoke({
            "history": self.history,
            "input": user_input
        })
        
        self.history.append(HumanMessage(content=user_input))
        self.history.append(AIMessage(content=response))
        
        return response

class WindowMemoryChain:
    """带有窗口记忆的链"""
    
    def __init__(self, llm, window_size: int = 6):
        self.llm = llm
        self.window_size = window_size
        self.history: List[BaseMessage] = []
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个友好的AI助手。基于最近的对话历史进行回复。"),
            MessagesPlaceholder(variable_name="recent_history"),
            ("human", "{input}")
        ])
        
        def get_recent_history(inputs: dict) -> dict:
            recent = self.history[-self.window_size:] if len(self.history) > self.window_size else self.history
            return {
                "recent_history": recent,
                "input": inputs["input"]
            }
        
        self.chain = (
            RunnableLambda(get_recent_history) |
            self.prompt |
            self.llm |
            StrOutputParser()
        )
    
    def invoke(self, user_input: str) -> str:
        response = self.chain.invoke({"input": user_input})
        
        self.history.append(HumanMessage(content=user_input))
        self.history.append(AIMessage(content=response))
        
        return response
    
    def get_window_info(self) -> dict:
        return {
            "total_messages": len(self.history),
            "window_size": self.window_size,
            "messages_in_window": min(len(self.history), self.window_size)
        }

# ===================== 测试函数 =====================

def test_manual_memory():
    """测试手动记忆管理"""
    print("=" * 50)
    print("测试手动记忆管理")
    print("=" * 50)
    
    llm = create_llm()
    chain = ManualMemoryChain(llm)
    
    conversations = [
        "你好，我叫张三，是一名老师",
        "我在北京工作",
        "你还记得我的名字吗？",
        "我在哪里工作？"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        try:
            response = chain.invoke(user_input)
            print(f"\n第{i}轮:")
            print(f"用户: {user_input}")
            print(f"AI: {response}")
        except Exception as e:
            print(f"错误: {e}")

def test_runnable_with_history():
    """测试 RunnableWithMessageHistory"""
    print("\n\n" + "=" * 50)
    print("测试 RunnableWithMessageHistory")
    print("=" * 50)
    
    llm = create_llm()
    
    # 存储会话历史
    store = {}
    
    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]
    
    # 创建链
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的AI助手。请根据对话历史进行回复。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    
    base_chain = prompt | llm | StrOutputParser()
    
    chain_with_history = RunnableWithMessageHistory(
        base_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    
    config = {"configurable": {"session_id": "test_session"}}
    
    conversations = [
        "我是李四，我喜欢编程",
        "我最喜欢Python语言",
        "你记得我的爱好吗？",
        "我喜欢什么编程语言？"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        try:
            response = chain_with_history.invoke(
                {"input": user_input},
                config=config
            )
            print(f"\n第{i}轮:")
            print(f"用户: {user_input}")
            print(f"AI: {response}")
        except Exception as e:
            print(f"错误: {e}")

def test_window_memory():
    """测试窗口记忆"""
    print("\n\n" + "=" * 50)
    print("测试窗口记忆 (窗口大小=4)")
    print("=" * 50)
    
    llm = create_llm()
    chain = WindowMemoryChain(llm, window_size=4)
    
    conversations = [
        "我叫王五，是医生",
        "我在上海工作",
        "我喜欢阅读",
        "我有一只狗",
        "我的狗叫小黑",
        "你还记得我的名字吗？",  # 可能已经超出窗口
        "我的宠物是什么？",      # 应该还记得
    ]
    
    for i, user_input in enumerate(conversations, 1):
        try:
            response = chain.invoke(user_input)
            print(f"\n第{i}轮:")
            print(f"用户: {user_input}")
            print(f"AI: {response}")
            
            info = chain.get_window_info()
            print(f"窗口状态: {info['messages_in_window']}/{info['window_size']} (总计: {info['total_messages']})")
        except Exception as e:
            print(f"错误: {e}")

def interactive_demo():
    """交互式演示"""
    print("\n\n" + "=" * 50)
    print("交互式LCEL记忆演示")
    print("=" * 50)
    
    print("\n选择记忆实现方式:")
    print("1. 手动管理历史")
    print("2. 窗口记忆")
    
    choice = input("请选择 (1-2): ").strip()
    
    llm = create_llm()
    
    if choice == "1":
        chain = ManualMemoryChain(llm)
        print("\n使用手动管理历史，输入 'quit' 退出")
        
        while True:
            user_input = input("\n你: ").strip()
            if user_input.lower() == 'quit':
                break
            if not user_input:
                continue
                
            try:
                response = chain.invoke(user_input)
                print(f"AI: {response}")
            except Exception as e:
                print(f"错误: {e}")
                
    elif choice == "2":
        chain = WindowMemoryChain(llm, window_size=6)
        print("\n使用窗口记忆 (窗口大小=6)，输入 'quit' 退出")
        
        while True:
            user_input = input("\n你: ").strip()
            if user_input.lower() == 'quit':
                break
            if not user_input:
                continue
                
            try:
                response = chain.invoke(user_input)
                print(f"AI: {response}")
                info = chain.get_window_info()
                print(f"[窗口: {info['messages_in_window']}/{info['window_size']}]")
            except Exception as e:
                print(f"错误: {e}")
    else:
        print("无效选择")

def main():
    """主函数"""
    print("LCEL 对话记忆系统测试")
    print("=" * 40)
    
    try:
        llm = create_llm()
        test_response = llm.invoke("Hello")
        print(f"✓ 成功连接到 Ollama ({OLLAMA_MODEL})")
    except Exception as e:
        print(f"✗ 连接 Ollama 失败: {e}")
        print("请确保 Ollama 正在运行并且已安装指定模型")
        return
    
    while True:
        print("\n请选择测试模式:")
        print("1. 测试手动记忆管理")
        print("2. 测试 RunnableWithMessageHistory")
        print("3. 测试窗口记忆")
        print("4. 交互式演示")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            test_manual_memory()
        elif choice == "2":
            test_runnable_with_history()
        elif choice == "3":
            test_window_memory()
        elif choice == "4":
            interactive_demo()
        elif choice == "5":
            print("再见！")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
