#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LangChain 记忆对话系统运行脚本
简化版本，用于快速测试不同的记忆类型
"""

import os
import sys
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# LangChain imports
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory,
)
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM  # 使用新的导入

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

def test_memory_type(memory_type: str, llm):
    """测试指定的记忆类型"""
    print(f"\n{'='*50}")
    print(f"测试 {memory_type}")
    print(f"{'='*50}")
    
    # 创建通用的prompt模板
    from langchain.prompts import PromptTemplate

    prompt_template = PromptTemplate(
        input_variables=["history", "input"],
        template="""以下是人类和AI之间的友好对话。AI很健谈，并根据其上下文提供大量具体细节。如果AI不知道问题的答案，它会诚实地说不知道。

当前对话:
{history}
人类: {input}
AI:"""
    )

    # 创建不同类型的记忆
    if memory_type == "buffer":
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )
        print("使用 ConversationBufferMemory - 保存完整对话历史")

    elif memory_type == "window":
        memory = ConversationBufferWindowMemory(
            k=3,  # 保留最近3轮对话
            return_messages=True,
            memory_key="history"
        )
        print("使用 ConversationBufferWindowMemory - 保留最近3轮对话")

    elif memory_type == "summary":
        memory = ConversationSummaryMemory(
            llm=llm,
            return_messages=True,
            memory_key="history"
        )
        print("使用 ConversationSummaryMemory - 总结历史对话")

    elif memory_type == "summary_buffer":
        memory = ConversationSummaryBufferMemory(
            llm=llm,
            max_token_limit=200,
            return_messages=True,
            memory_key="history"
        )
        print("使用 ConversationSummaryBufferMemory - 摘要+缓冲记忆")

    else:
        raise ValueError(f"不支持的记忆类型: {memory_type}")

    # 创建对话链
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt_template,
        verbose=False
    )
    
    # 测试对话
    test_conversations = [
        "你好，我叫小明，是一名程序员",
        "我在北京工作，专门做Python开发",
        "我最近在学习机器学习和深度学习",
        "我对LangChain这个框架很感兴趣",
        "我想用它来构建智能对话系统",
        "你还记得我的名字和职业吗？",
        "我在哪个城市工作？",
        "我最近在学习什么技术？"
    ]
    
    for i, user_input in enumerate(test_conversations, 1):
        try:
            response = conversation.predict(input=user_input)
            print(f"\n第{i}轮对话:")
            print(f"用户: {user_input}")
            print(f"AI: {response}")
            
            # 显示记忆状态
            if hasattr(memory, 'chat_memory'):
                msg_count = len(memory.chat_memory.messages)
                print(f"当前记忆中的消息数: {msg_count}")
                
            if hasattr(memory, 'moving_summary_buffer') and memory.moving_summary_buffer:
                print(f"当前摘要: {memory.moving_summary_buffer[:100]}...")
                
        except Exception as e:
            print(f"对话出错: {e}")
            continue
    
    return memory

def interactive_chat(memory_type: str = "summary_buffer"):
    """交互式聊天模式"""
    print(f"\n{'='*50}")
    print(f"交互式聊天模式 - 使用 {memory_type} 记忆")
    print("输入 'quit' 退出，输入 'memory' 查看记忆状态")
    print(f"{'='*50}")
    
    llm = create_llm()

    # 创建prompt模板
    from langchain.prompts import PromptTemplate

    prompt_template = PromptTemplate(
        input_variables=["history", "input"],
        template="""以下是人类和AI之间的友好对话。AI很健谈，并根据其上下文提供大量具体细节。如果AI不知道问题的答案，它会诚实地说不知道。

当前对话:
{history}
人类: {input}
AI:"""
    )

    # 创建记忆
    if memory_type == "buffer":
        memory = ConversationBufferMemory(return_messages=True, memory_key="history")
    elif memory_type == "window":
        memory = ConversationBufferWindowMemory(k=5, return_messages=True, memory_key="history")
    elif memory_type == "summary":
        memory = ConversationSummaryMemory(llm=llm, return_messages=True, memory_key="history")
    else:  # summary_buffer
        memory = ConversationSummaryBufferMemory(
            llm=llm, max_token_limit=300, return_messages=True, memory_key="history"
        )

    conversation = ConversationChain(llm=llm, memory=memory, prompt=prompt_template, verbose=False)
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            elif user_input.lower() == 'memory':
                print(f"\n记忆状态:")
                if hasattr(memory, 'chat_memory'):
                    print(f"消息数: {len(memory.chat_memory.messages)}")
                if hasattr(memory, 'moving_summary_buffer') and memory.moving_summary_buffer:
                    print(f"摘要: {memory.moving_summary_buffer}")
                continue
            elif not user_input:
                continue
            
            response = conversation.predict(input=user_input)
            print(f"AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"出错了: {e}")

def main():
    """主函数"""
    print("LangChain 记忆对话系统测试")
    print("=" * 40)
    
    try:
        llm = create_llm()
        print(f"✓ 成功连接到 Ollama ({OLLAMA_MODEL})")
    except Exception as e:
        print(f"✗ 连接 Ollama 失败: {e}")
        print("请确保 Ollama 正在运行并且已安装指定模型")
        return
    
    while True:
        print("\n请选择测试模式:")
        print("1. 自动测试所有记忆类型")
        print("2. 测试特定记忆类型")
        print("3. 交互式聊天")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            # 测试所有记忆类型
            memory_types = ["buffer", "window", "summary", "summary_buffer"]
            for memory_type in memory_types:
                try:
                    test_memory_type(memory_type, llm)
                except Exception as e:
                    print(f"测试 {memory_type} 时出错: {e}")
                    
        elif choice == "2":
            print("\n可用的记忆类型:")
            print("1. buffer - 基础缓冲记忆")
            print("2. window - 窗口缓冲记忆")
            print("3. summary - 摘要记忆")
            print("4. summary_buffer - 摘要缓冲记忆")
            
            memory_choice = input("请选择记忆类型 (1-4): ").strip()
            memory_map = {"1": "buffer", "2": "window", "3": "summary", "4": "summary_buffer"}
            
            if memory_choice in memory_map:
                try:
                    test_memory_type(memory_map[memory_choice], llm)
                except Exception as e:
                    print(f"测试出错: {e}")
            else:
                print("无效选择")
                
        elif choice == "3":
            print("\n选择交互模式的记忆类型:")
            print("1. buffer")
            print("2. window") 
            print("3. summary")
            print("4. summary_buffer (推荐)")
            
            memory_choice = input("请选择 (1-4, 默认4): ").strip() or "4"
            memory_map = {"1": "buffer", "2": "window", "3": "summary", "4": "summary_buffer"}
            
            if memory_choice in memory_map:
                interactive_chat(memory_map[memory_choice])
            else:
                print("无效选择，使用默认的 summary_buffer")
                interactive_chat("summary_buffer")
                
        elif choice == "4":
            print("再见！")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
