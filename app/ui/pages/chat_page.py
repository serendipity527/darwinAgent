"""
聊天页面组件
"""

import gradio as gr
from typing import List, Dict, Any


def create_chat_page():
    """
    创建聊天页面
    
    Returns:
        list: 聊天页面组件列表
    """
    with gr.Column() as chat_page:
        # 聊天历史
        chatbot = gr.Chatbot(
            height=500,
            show_copy_button=True,
            elem_id="chatbot",
            label="对话历史"
        )
        
        # 输入区域
        with gr.Row():
            with gr.Column(scale=8):
                user_input = gr.Textbox(
                    placeholder="在这里输入您的问题...",
                    label="用户输入",
                    lines=2,
                    elem_id="user-input"
                )
            
            with gr.Column(scale=1):
                submit_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空")
        
        # 高级选项
        with gr.Accordion("高级选项", open=False):
            with gr.Row():
                agent_type = gr.Dropdown(
                    choices=["聊天代理", "搜索代理", "推理代理"],
                    value="聊天代理",
                    label="代理类型"
                )
                
                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.7,
                    step=0.1,
                    label="温度"
                )
        
        # 状态
        conversation_state = gr.State({})
    
    # 注册回调
    submit_btn.click(
        fn=mock_chat_response,
        inputs=[user_input, chatbot, conversation_state, agent_type, temperature],
        outputs=[chatbot, user_input, conversation_state]
    )
    
    clear_btn.click(
        fn=lambda: ([], "", {}),
        inputs=[],
        outputs=[chatbot, user_input, conversation_state]
    )
    
    return chat_page


def mock_chat_response(
    user_input: str,
    history: List[List[str]],
    state: Dict[str, Any],
    agent_type: str,
    temperature: float
) -> tuple:
    """
    模拟聊天响应（实际项目中应替换为真实的代理调用）
    
    Args:
        user_input: 用户输入
        history: 聊天历史
        state: 对话状态
        agent_type: 代理类型
        temperature: 温度参数
        
    Returns:
        tuple: 更新后的历史、清空的用户输入和更新后的状态
    """
    if not user_input.strip():
        return history, "", state
    
    # 更新历史
    history.append([user_input, None])
    
    # 模拟回复
    reply = f"您选择了{agent_type}，温度设置为{temperature}。\n\n您的输入是：{user_input}\n\n这是一个模拟回复，实际项目中应替换为真实的代理响应。"
    
    # 更新历史和状态
    history[-1][1] = reply
    state["last_input"] = user_input
    state["last_agent"] = agent_type
    
    return history, "", state 