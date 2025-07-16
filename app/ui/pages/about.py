"""
关于页面组件
"""

import gradio as gr


def create_about_page():
    """
    创建关于页面
    
    Returns:
        list: 关于页面组件列表
    """
    with gr.Column() as about_page:
        gr.Markdown("""
        # 关于 Darwin Agent
        
        Darwin Agent 是一个使用 FastAPI、LangChain 和 LangGraph 构建的智能代理系统。
        
        ## 技术栈
        
        - **后端框架**: FastAPI
        - **代理框架**: LangChain, LangGraph
        - **前端界面**: Gradio
        - **向量存储**: Chroma, FAISS
        
        ## 项目结构
        
        项目采用模块化设计，主要包括以下组件：
        
        - **API层**: 处理HTTP请求和响应
        - **代理层**: 实现各种智能代理
        - **工作流层**: 使用LangGraph定义代理工作流
        - **链层**: 使用LangChain定义处理链
        - **服务层**: 提供业务逻辑和外部服务集成
        - **UI层**: 使用Gradio提供用户界面
        
        ## 联系方式
        
        如有问题或建议，请联系项目维护者。
        """)
        
        with gr.Row():
            gr.Markdown("© 2023 Darwin Agent Team")
    
    return about_page 