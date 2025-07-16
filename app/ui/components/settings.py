"""
设置界面组件
"""

import gradio as gr
from typing import Callable, Dict, Any


def create_settings_interface(
    on_save: Callable[[Dict[str, Any]], Any] = None,
    on_reset: Callable[[], Any] = None,
    default_settings: Dict[str, Any] = None,
    **kwargs
):
    """
    创建设置界面组件
    
    Args:
        on_save: 保存设置回调函数
        on_reset: 重置设置回调函数
        default_settings: 默认设置
        **kwargs: 其他参数
        
    Returns:
        tuple: 设置界面组件元组 (settings_components, save_btn, reset_btn)
    """
    if default_settings is None:
        default_settings = {}
    
    settings_components = {}
    
    with gr.Column() as settings_container:
        gr.Markdown("## 代理设置")
        
        with gr.Row():
            settings_components["agent_type"] = gr.Dropdown(
                choices=["聊天代理", "搜索代理", "推理代理"],
                value=default_settings.get("agent_type", "聊天代理"),
                label="默认代理类型"
            )
        
        gr.Markdown("## 模型设置")
        
        with gr.Row():
            settings_components["model"] = gr.Dropdown(
                choices=["gpt-3.5-turbo", "gpt-4", "claude-3-opus", "claude-3-sonnet"],
                value=default_settings.get("model", "gpt-3.5-turbo"),
                label="默认模型"
            )
            
            settings_components["temperature"] = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                value=default_settings.get("temperature", 0.7),
                step=0.1,
                label="默认温度"
            )
        
        gr.Markdown("## 界面设置")
        
        with gr.Row():
            settings_components["theme"] = gr.Dropdown(
                choices=["默认", "暗色", "亮色"],
                value=default_settings.get("theme", "默认"),
                label="界面主题"
            )
            
            settings_components["language"] = gr.Dropdown(
                choices=["中文", "English"],
                value=default_settings.get("language", "中文"),
                label="界面语言"
            )
        
        with gr.Row():
            save_btn = gr.Button("保存设置", variant="primary")
            reset_btn = gr.Button("重置设置")
        
        # 注册回调
        if on_save:
            save_btn.click(
                fn=lambda **kwargs: on_save(kwargs),
                inputs=list(settings_components.values()),
                outputs=[]
            )
        
        if on_reset:
            reset_btn.click(
                fn=on_reset,
                inputs=[],
                outputs=list(settings_components.values())
            )
    
    return settings_components, save_btn, reset_btn 