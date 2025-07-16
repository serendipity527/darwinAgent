"""
搜索界面组件
"""

import gradio as gr
from typing import Callable, List, Dict, Any


def create_search_interface(
    on_search: Callable[..., Any] = None,
    **kwargs
):
    """
    创建搜索界面组件
    
    Args:
        on_search: 搜索回调函数
        **kwargs: 其他参数
        
    Returns:
        tuple: 搜索界面组件元组 (query_input, search_btn, results_box)
    """
    with gr.Column() as search_container:
        # 搜索输入
        with gr.Row():
            query_input = gr.Textbox(
                placeholder="输入搜索关键词...",
                label="搜索查询",
                elem_id="search-input"
            )
            search_btn = gr.Button("搜索", variant="primary")
        
        # 搜索选项
        with gr.Row():
            search_type = gr.Dropdown(
                choices=["文档", "网络", "知识库"],
                value="文档",
                label="搜索类型"
            )
            
            max_results = gr.Slider(
                minimum=1,
                maximum=20,
                value=5,
                step=1,
                label="最大结果数"
            )
        
        # 结果显示
        results_box = gr.Dataframe(
            headers=["标题", "内容", "相关度"],
            label="搜索结果",
            elem_id="search-results",
            interactive=False,
            wrap=True
        )
        
        # 注册回调
        if on_search:
            search_btn.click(
                fn=on_search,
                inputs=[query_input, search_type, max_results],
                outputs=[results_box]
            )
    
    return query_input, search_btn, results_box 