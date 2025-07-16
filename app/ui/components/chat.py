"""
聊天界面组件
"""

import gradio as gr
from typing import Callable, Dict, Any


def create_chat_interface(
    on_submit: Callable = None,
    on_clear: Callable = None,
    **kwargs
):
    """
    创建聊天界面组件
    
    Args:
        on_submit: 提交回调函数
        on_clear: 清空回调函数
        **kwargs: 其他参数
        
    Returns:
        tuple: 聊天界面组件元组 (chatbot, user_input, submit_btn, clear_btn)
    """
    # 聊天历史
    chatbot = gr.Chatbot(
        height=kwargs.get("height", 500),
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
                lines=kwargs.get("lines", 2),
                elem_id="user-input"
            )
        
        with gr.Column(scale=1):
            submit_btn = gr.Button("发送", variant="primary")
            clear_btn = gr.Button("清空")
    
    # 注册回调
    if on_submit:
        submit_btn.click(fn=on_submit)
    
    if on_clear:
        clear_btn.click(fn=on_clear)
    
    return chatbot, user_input, submit_btn, clear_btn 