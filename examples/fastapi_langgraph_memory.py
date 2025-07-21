#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastAPI + LangGraph 记忆对话 API 服务
提供RESTful API接口的记忆对话系统
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
from typing_extensions import TypedDict
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import OllamaLLM

# ===================== 配置部分 =====================

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma:3b"

# 全局变量
chat_app = None
llm = None

# ===================== Pydantic 模型 =====================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID，如果不提供将自动生成")
    user_id: Optional[str] = Field(None, description="用户ID")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str = Field(..., description="AI回复")
    session_id: str = Field(..., description="会话ID")
    user_info: Dict[str, Any] = Field(default_factory=dict, description="用户信息")
    processing_time: float = Field(..., description="处理时间（秒）")
    message_count: int = Field(..., description="当前会话消息数量")

class ConversationHistory(BaseModel):
    """对话历史模型"""
    session_id: str = Field(..., description="会话ID")
    messages: List[Dict[str, str]] = Field(..., description="消息列表")
    user_info: Dict[str, Any] = Field(default_factory=dict, description="用户信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话ID")
    message_count: int = Field(..., description="消息数量")
    user_info: Dict[str, Any] = Field(default_factory=dict, description="用户信息")
    last_activity: datetime = Field(default_factory=datetime.now, description="最后活动时间")

# ===================== LangGraph 状态和节点 =====================

class APIState(TypedDict):
    """API状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_info: Dict[str, Any]
    session_metadata: Dict[str, Any]

async def extract_user_info_async(messages: List[BaseMessage]) -> Dict[str, Any]:
    """异步提取用户信息"""
    user_info = {}
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content.lower()
            
            # 提取姓名
            if "我叫" in content or "我是" in content:
                words = content.split()
                for i, word in enumerate(words):
                    if word in ["我叫", "我是"] and i + 1 < len(words):
                        name = words[i + 1].replace("，", "").replace(",", "")
                        if name and len(name) < 10:  # 简单验证
                            user_info["name"] = name
                        break
            
            # 提取职业
            jobs = ["程序员", "工程师", "老师", "医生", "学生", "设计师", "销售", "经理"]
            for job in jobs:
                if job in content:
                    user_info["job"] = job
                    break
            
            # 提取爱好
            if "喜欢" in content:
                user_info["interests"] = content
            
            # 提取位置
            cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉"]
            for city in cities:
                if city in content:
                    user_info["location"] = city
                    break
    
    return user_info

async def api_chatbot_node(state: APIState):
    """API聊天机器人节点"""
    start_time = asyncio.get_event_loop().time()
    
    # 提取用户信息
    user_info = await extract_user_info_async(state["messages"])
    
    # 更新用户信息
    existing_user_info = state.get("user_info", {})
    existing_user_info.update(user_info)
    
    # 创建系统消息
    user_context = ""
    if existing_user_info:
        user_context = f"用户信息: {existing_user_info}\n\n"
    
    system_content = f"""你是一个友好的AI助手，能记住对话历史。

{user_context}请基于用户信息和对话历史进行个性化回复。保持回复简洁明了。"""
    
    system_message = SystemMessage(content=system_content)
    messages = [system_message] + state["messages"]
    
    # 异步调用LLM
    response = await asyncio.to_thread(llm.invoke, messages)
    
    processing_time = asyncio.get_event_loop().time() - start_time
    
    # 更新会话元数据
    session_metadata = state.get("session_metadata", {})
    session_metadata.update({
        "last_activity": datetime.now().isoformat(),
        "processing_time": processing_time
    })
    
    return {
        "messages": [AIMessage(content=response)],
        "user_info": existing_user_info,
        "session_metadata": session_metadata
    }

def create_api_chat_graph():
    """创建API聊天图"""
    graph = StateGraph(APIState)
    
    # 添加节点
    graph.add_node("chatbot", api_chatbot_node)
    
    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # 添加内存检查点
    memory = MemorySaver()
    
    # 编译图
    return graph.compile(checkpointer=memory)

# ===================== 应用初始化 =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global chat_app, llm
    
    # 启动时初始化
    print("初始化 LangGraph 聊天应用...")
    
    try:
        llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0.7
        )
        
        # 测试连接
        await asyncio.to_thread(llm.invoke, "Hello")
        print("✓ Ollama 连接成功")
        
        chat_app = create_api_chat_graph()
        print("✓ LangGraph 应用初始化成功")
        
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        raise
    
    yield
    
    # 关闭时清理
    print("清理资源...")

# 创建FastAPI应用
app = FastAPI(
    title="LangGraph 记忆对话 API",
    description="基于 LangGraph 的记忆对话系统 RESTful API",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== API 路由 =====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "LangGraph 记忆对话 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送聊天消息"""
    if not chat_app:
        raise HTTPException(status_code=500, detail="聊天应用未初始化")
    
    # 生成会话ID（如果未提供）
    session_id = request.session_id or str(uuid.uuid4())
    
    # 配置
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # 调用聊天应用
        result = await chat_app.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        # 获取当前状态以计算消息数量
        state = await chat_app.aget_state(config)
        message_count = len(state.values.get("messages", []))
        
        return ChatResponse(
            response=result["messages"][-1].content,
            session_id=session_id,
            user_info=result.get("user_info", {}),
            processing_time=total_time,
            message_count=message_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

@app.get("/conversations/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """获取对话历史"""
    if not chat_app:
        raise HTTPException(status_code=500, detail="聊天应用未初始化")
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        state = await chat_app.aget_state(config)
        messages = state.values.get("messages", [])
        user_info = state.values.get("user_info", {})
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return ConversationHistory(
            session_id=session_id,
            messages=formatted_messages,
            user_info=user_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")

@app.get("/sessions/{session_id}/info", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """获取会话信息"""
    if not chat_app:
        raise HTTPException(status_code=500, detail="聊天应用未初始化")
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        state = await chat_app.aget_state(config)
        
        if not state.values:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        messages = state.values.get("messages", [])
        user_info = state.values.get("user_info", {})
        session_metadata = state.values.get("session_metadata", {})
        
        last_activity_str = session_metadata.get("last_activity")
        last_activity = datetime.fromisoformat(last_activity_str) if last_activity_str else datetime.now()
        
        return SessionInfo(
            session_id=session_id,
            message_count=len(messages),
            user_info=user_info,
            last_activity=last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话（注意：LangGraph的MemorySaver不支持删除，这里只是示例）"""
    # 实际上MemorySaver不支持删除操作
    # 在生产环境中，你可能需要使用支持删除的检查点存储
    return {"message": f"会话 {session_id} 删除请求已接收（注意：内存存储不支持真正删除）"}

@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """清空会话（创建新的会话ID）"""
    new_session_id = str(uuid.uuid4())
    return {
        "message": "会话已清空",
        "old_session_id": session_id,
        "new_session_id": new_session_id
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        if llm:
            # 测试LLM连接
            await asyncio.to_thread(llm.invoke, "test")
            return {"status": "healthy", "llm": "connected"}
        else:
            return {"status": "unhealthy", "llm": "not_initialized"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# ===================== 批量处理API =====================

class BatchChatRequest(BaseModel):
    """批量聊天请求"""
    messages: List[str] = Field(..., description="消息列表")
    session_id: Optional[str] = Field(None, description="会话ID")

class BatchChatResponse(BaseModel):
    """批量聊天响应"""
    responses: List[ChatResponse] = Field(..., description="响应列表")
    total_time: float = Field(..., description="总处理时间")

@app.post("/chat/batch", response_model=BatchChatResponse)
async def batch_chat(request: BatchChatRequest):
    """批量处理聊天消息"""
    if not chat_app:
        raise HTTPException(status_code=500, detail="聊天应用未初始化")
    
    session_id = request.session_id or str(uuid.uuid4())
    start_time = asyncio.get_event_loop().time()
    
    responses = []
    
    try:
        for i, message in enumerate(request.messages):
            # 为批量处理创建子会话
            sub_session_id = f"{session_id}_batch_{i}"
            
            chat_request = ChatRequest(
                message=message,
                session_id=sub_session_id
            )
            
            response = await chat(chat_request)
            responses.append(response)
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        return BatchChatResponse(
            responses=responses,
            total_time=total_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")

# ===================== WebSocket 支持 =====================

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket聊天接口"""
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            if not chat_app:
                await websocket.send_json({"error": "聊天应用未初始化"})
                continue
            
            try:
                # 处理消息
                config = {"configurable": {"thread_id": session_id}}
                
                result = await chat_app.ainvoke(
                    {"messages": [HumanMessage(content=data)]},
                    config=config
                )
                
                # 发送响应
                response = {
                    "response": result["messages"][-1].content,
                    "user_info": result.get("user_info", {}),
                    "session_id": session_id
                }
                
                await websocket.send_json(response)
                
            except Exception as e:
                await websocket.send_json({"error": f"处理失败: {str(e)}"})
                
    except WebSocketDisconnect:
        print(f"WebSocket连接断开: {session_id}")

# ===================== 运行服务器 =====================

if __name__ == "__main__":
    import uvicorn

    print("启动 LangGraph 记忆对话 API 服务器...")
    print("API文档: http://localhost:8000/docs")
    print("WebSocket测试: ws://localhost:8000/ws/test_session")
    print("健康检查: http://localhost:8000/health")

    uvicorn.run(
        "fastapi_langgraph_memory:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
