"""
Gradio UI 回调函数
"""

import gradio as gr
from typing import Dict, Any


def register_callbacks(demo: gr.Blocks):
    """
    注册全局回调函数
    
    Args:
        demo: Gradio应用实例
    """
    # 这里可以注册全局回调函数
    pass


def handle_error(fn):
    """
    错误处理装饰器
    
    Args:
        fn: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            gr.Warning(f"发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    return wrapper


def update_ui_theme(theme_name: str):
    """
    更新UI主题
    
    Args:
        theme_name: 主题名称
        
    Returns:
        dict: Gradio更新指令
    """
    theme_map = {
        "默认": gr.themes.Soft(),
        "暗色": gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        "亮色": gr.themes.Soft(primary_hue="indigo", neutral_hue="zinc")
    }
    
    theme = theme_map.get(theme_name, gr.themes.Soft())
    
    return {
        "theme": theme
    }


def load_settings() -> Dict[str, Any]:
    """
    加载设置
    
    Returns:
        Dict[str, Any]: 设置字典
    """
    # 实际项目中应从数据库或配置文件加载
    return {
        "agent_type": "聊天代理",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "theme": "默认",
        "language": "中文"
    }


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    保存设置
    
    Args:
        settings: 设置字典
        
    Returns:
        bool: 是否保存成功
    """
    # 实际项目中应保存到数据库或配置文件
    print(f"保存设置: {settings}")
    return True 