"""
首页组件
"""

import gradio as gr


def create_home_page():
    """
    创建首页
    
    Returns:
        list: 首页组件列表
    """
    with gr.Column() as home_page:
        gr.Markdown("""
        # 欢迎使用 Darwin Agent
        
        这是一个基于 LangChain 和 LangGraph 构建的智能代理系统。
        
        ## 功能特点
        
        - 基于 FastAPI 的高性能 API 服务
        - 使用 LangChain 构建灵活的处理链
        - 使用 LangGraph 设计复杂的代理工作流
        - Gradio 提供友好的用户界面
        - 模块化设计，易于扩展和自定义
        
        ## 开始使用
        
        点击上方的"聊天"按钮开始与代理交流。
        """)
        
        with gr.Row():
            chat_btn = gr.Button("开始聊天", variant="primary")
            about_btn = gr.Button("了解更多")
    
    return home_page 