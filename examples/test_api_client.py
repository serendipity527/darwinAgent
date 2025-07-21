#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LangGraph 记忆对话 API 客户端测试
测试 FastAPI + LangGraph 记忆对话系统的各种功能
"""

import asyncio
import aiohttp
import websockets
import json
from typing import Dict, List, Any

# API 配置
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

class LangGraphAPIClient:
    """LangGraph API 客户端"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
    
    async def chat(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """发送聊天消息"""
        data = {"message": message}
        if session_id:
            data["session_id"] = session_id
        
        async with self.session.post(f"{self.base_url}/chat", json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API错误 {response.status}: {error}")
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """获取对话历史"""
        async with self.session.get(f"{self.base_url}/conversations/{session_id}") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API错误 {response.status}: {error}")
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        async with self.session.get(f"{self.base_url}/sessions/{session_id}/info") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API错误 {response.status}: {error}")
    
    async def batch_chat(self, messages: List[str], session_id: str = None) -> Dict[str, Any]:
        """批量聊天"""
        data = {"messages": messages}
        if session_id:
            data["session_id"] = session_id
        
        async with self.session.post(f"{self.base_url}/chat/batch", json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API错误 {response.status}: {error}")
    
    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """清空会话"""
        async with self.session.post(f"{self.base_url}/sessions/{session_id}/clear") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API错误 {response.status}: {error}")

# ===================== 测试函数 =====================

async def test_health_check():
    """测试健康检查"""
    print("=== 健康检查测试 ===")
    
    async with LangGraphAPIClient() as client:
        try:
            health = await client.health_check()
            print(f"健康状态: {health}")
            return health.get("status") == "healthy"
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False

async def test_basic_chat():
    """测试基础聊天功能"""
    print("\n=== 基础聊天测试 ===")
    
    async with LangGraphAPIClient() as client:
        session_id = "test_basic_chat"
        
        conversations = [
            "你好，我叫Alice，是一名数据科学家",
            "我在研究机器学习算法",
            "你还记得我的名字吗？",
            "我的职业是什么？"
        ]
        
        for i, message in enumerate(conversations, 1):
            try:
                response = await client.chat(message, session_id)
                print(f"\n第{i}轮:")
                print(f"用户: {message}")
                print(f"AI: {response['response']}")
                print(f"处理时间: {response['processing_time']:.3f}s")
                print(f"消息数: {response['message_count']}")
                
                if response.get('user_info'):
                    print(f"用户信息: {response['user_info']}")
                    
            except Exception as e:
                print(f"聊天失败: {e}")

async def test_conversation_history():
    """测试对话历史功能"""
    print("\n=== 对话历史测试 ===")
    
    async with LangGraphAPIClient() as client:
        session_id = "test_history"
        
        # 先进行一些对话
        messages = [
            "你好，我是Bob",
            "我是一名程序员",
            "我喜欢Python编程"
        ]
        
        for message in messages:
            await client.chat(message, session_id)
        
        # 获取对话历史
        try:
            history = await client.get_conversation_history(session_id)
            print(f"会话ID: {history['session_id']}")
            print(f"用户信息: {history['user_info']}")
            print("对话历史:")
            
            for msg in history['messages']:
                role = "用户" if msg['role'] == "user" else "AI"
                print(f"  {role}: {msg['content']}")
                
        except Exception as e:
            print(f"获取历史失败: {e}")

async def test_session_info():
    """测试会话信息功能"""
    print("\n=== 会话信息测试 ===")
    
    async with LangGraphAPIClient() as client:
        session_id = "test_session_info"
        
        # 先发送一些消息
        await client.chat("你好，我是Charlie，我是设计师", session_id)
        await client.chat("我在上海工作", session_id)
        
        # 获取会话信息
        try:
            info = await client.get_session_info(session_id)
            print(f"会话信息: {info}")
            
        except Exception as e:
            print(f"获取会话信息失败: {e}")

async def test_batch_chat():
    """测试批量聊天功能"""
    print("\n=== 批量聊天测试 ===")
    
    async with LangGraphAPIClient() as client:
        messages = [
            "你好，我叫David",
            "我是一名老师",
            "我在北京工作",
            "我喜欢阅读和旅行",
            "你能总结一下我的信息吗？"
        ]
        
        try:
            start_time = asyncio.get_event_loop().time()
            result = await client.batch_chat(messages, "test_batch")
            total_time = asyncio.get_event_loop().time() - start_time
            
            print(f"批量处理完成，总耗时: {total_time:.3f}s")
            print(f"API报告的处理时间: {result['total_time']:.3f}s")
            
            for i, response in enumerate(result['responses'], 1):
                print(f"\n消息 {i}: {messages[i-1]}")
                print(f"回复: {response['response']}")
                print(f"处理时间: {response['processing_time']:.3f}s")
                
        except Exception as e:
            print(f"批量聊天失败: {e}")

async def test_websocket_chat():
    """测试WebSocket聊天功能"""
    print("\n=== WebSocket聊天测试 ===")
    
    session_id = "test_websocket"
    uri = f"{WS_BASE_URL}/ws/{session_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            messages = [
                "你好，我是Eve",
                "我是一名销售",
                "你还记得我的名字吗？"
            ]
            
            for i, message in enumerate(messages, 1):
                # 发送消息
                await websocket.send(message)
                print(f"\n第{i}轮:")
                print(f"用户: {message}")
                
                # 接收响应
                response = await websocket.recv()
                data = json.loads(response)
                
                if "error" in data:
                    print(f"错误: {data['error']}")
                else:
                    print(f"AI: {data['response']}")
                    if data.get('user_info'):
                        print(f"用户信息: {data['user_info']}")
                        
    except Exception as e:
        print(f"WebSocket聊天失败: {e}")

async def test_concurrent_sessions():
    """测试并发会话"""
    print("\n=== 并发会话测试 ===")
    
    async def chat_session(session_id: str, user_name: str, job: str):
        """单个会话的聊天"""
        async with LangGraphAPIClient() as client:
            messages = [
                f"你好，我是{user_name}",
                f"我是一名{job}",
                "你还记得我的名字吗？"
            ]
            
            results = []
            for message in messages:
                response = await client.chat(message, session_id)
                results.append(response)
            
            return session_id, user_name, results
    
    # 创建多个并发会话
    sessions = [
        ("session_1", "Alice", "程序员"),
        ("session_2", "Bob", "设计师"),
        ("session_3", "Charlie", "老师"),
        ("session_4", "David", "医生")
    ]
    
    start_time = asyncio.get_event_loop().time()
    
    tasks = [chat_session(sid, name, job) for sid, name, job in sessions]
    results = await asyncio.gather(*tasks)
    
    total_time = asyncio.get_event_loop().time() - start_time
    
    print(f"并发处理 {len(sessions)} 个会话，总耗时: {total_time:.3f}s")
    
    for session_id, user_name, session_results in results:
        print(f"\n会话 {session_id} ({user_name}):")
        for i, result in enumerate(session_results, 1):
            print(f"  第{i}轮: {result['response'][:50]}...")

async def test_performance():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    async with LangGraphAPIClient() as client:
        # 测试不同的并发级别
        concurrency_levels = [1, 5, 10]
        test_message = "你好，请介绍一下你自己"
        
        for concurrency in concurrency_levels:
            print(f"\n测试并发级别: {concurrency}")
            
            start_time = asyncio.get_event_loop().time()
            
            tasks = []
            for i in range(concurrency):
                session_id = f"perf_test_{concurrency}_{i}"
                tasks.append(client.chat(test_message, session_id))
            
            results = await asyncio.gather(*tasks)
            
            total_time = asyncio.get_event_loop().time() - start_time
            avg_time = total_time / concurrency
            
            print(f"总耗时: {total_time:.3f}s")
            print(f"平均耗时: {avg_time:.3f}s")
            print(f"QPS: {concurrency/total_time:.2f}")

# ===================== 主测试函数 =====================

async def run_all_tests():
    """运行所有测试"""
    print("LangGraph 记忆对话 API 测试")
    print("=" * 50)
    
    # 健康检查
    if not await test_health_check():
        print("❌ 服务不健康，停止测试")
        return
    
    print("✅ 服务健康，开始测试")
    
    # 运行各项测试
    tests = [
        test_basic_chat,
        test_conversation_history,
        test_session_info,
        test_batch_chat,
        test_websocket_chat,
        test_concurrent_sessions,
        test_performance
    ]
    
    for test_func in tests:
        try:
            await test_func()
            print(f"✅ {test_func.__name__} 测试完成")
        except Exception as e:
            print(f"❌ {test_func.__name__} 测试失败: {e}")
    
    print("\n🎉 所有测试完成！")

async def interactive_test():
    """交互式测试"""
    print("\n=== 交互式API测试 ===")
    print("输入 'quit' 退出")
    
    async with LangGraphAPIClient() as client:
        session_id = input("请输入会话ID (默认: interactive): ").strip() or "interactive"
        
        while True:
            try:
                user_input = input(f"\n[{session_id}] 你: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif not user_input:
                    continue
                
                response = await client.chat(user_input, session_id)
                print(f"AI: {response['response']}")
                print(f"(处理时间: {response['processing_time']:.3f}s, 消息数: {response['message_count']})")
                
                if response.get('user_info'):
                    print(f"用户信息: {response['user_info']}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")

# ===================== 主函数 =====================

async def main():
    """主函数"""
    print("LangGraph 记忆对话 API 客户端测试工具")
    print("=" * 50)
    print("请确保API服务器正在运行: python examples/fastapi_langgraph_memory.py")
    
    while True:
        print("\n请选择测试模式:")
        print("1. 运行所有测试")
        print("2. 健康检查")
        print("3. 基础聊天测试")
        print("4. 对话历史测试")
        print("5. 批量聊天测试")
        print("6. WebSocket测试")
        print("7. 并发测试")
        print("8. 性能测试")
        print("9. 交互式测试")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-9): ").strip()
        
        try:
            if choice == "1":
                await run_all_tests()
            elif choice == "2":
                await test_health_check()
            elif choice == "3":
                await test_basic_chat()
            elif choice == "4":
                await test_conversation_history()
            elif choice == "5":
                await test_batch_chat()
            elif choice == "6":
                await test_websocket_chat()
            elif choice == "7":
                await test_concurrent_sessions()
            elif choice == "8":
                await test_performance()
            elif choice == "9":
                await interactive_test()
            elif choice == "0":
                print("再见！")
                break
            else:
                print("无效选择，请重试")
                
        except Exception as e:
            print(f"测试执行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
