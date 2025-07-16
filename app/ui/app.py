"""
Gradio应用主入口
"""

import os
import gradio as gr
from typing import Dict, Any

# 导入页面组件
from app.ui.pages.home import create_home_page
from app.ui.pages.chat_page import create_chat_page
from app.ui.pages.about import create_about_page

# 导入工具函数
from app.ui.utils.callbacks import register_callbacks


def create_gradio_app() -> gr.Blocks:
    """
    创建Gradio应用
    
    Returns:
        gr.Blocks: Gradio应用实例
    """
    # 创建Gradio应用
    with gr.Blocks(title="Darwin Agent") as demo:
        # 创建导航栏
        with gr.Row(elem_id="navbar"):
            gr.Markdown("# Darwin Agent")
            
            with gr.Row():
                home_btn = gr.Button("首页", elem_id="nav-home")
                chat_btn = gr.Button("聊天", elem_id="nav-chat")
                about_btn = gr.Button("关于", elem_id="nav-about")
        
        # 创建页面容器
        with gr.Tabs(selected="home") as tabs:
            with gr.Tab(label="首页", id="home"):
                home_page = create_home_page()
            
            with gr.Tab(label="聊天", id="chat"):
                chat_page = create_chat_page()
                
            with gr.Tab(label="关于", id="about"):
                about_page = create_about_page()
        
        # 注册导航回调
        home_btn.click(lambda: gr.update(selected="home"), None, tabs)
        chat_btn.click(lambda: gr.update(selected="chat"), None, tabs)
        about_btn.click(lambda: gr.update(selected="about"), None, tabs)
        
        # 注册其他回调函数
        register_callbacks(demo)
    
    return demo


# 当作为模块导入时，提供创建应用的函数
create_app = create_gradio_app

# 当直接运行时，启动应用
if __name__ == "__main__":
    demo = create_gradio_app()
    demo.launch() 