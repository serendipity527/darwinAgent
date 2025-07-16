"""
默认主题配置
"""

import gradio as gr


def get_default_theme():
    """
    获取默认主题
    
    Returns:
        gr.Theme: Gradio主题对象
    """
    try:
        # Gradio 4.0+
        return gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="indigo",
            neutral_hue="slate"
        )
    except AttributeError:
        # 兼容旧版Gradio
        return None


def get_dark_theme():
    """
    获取暗色主题
    
    Returns:
        gr.Theme: Gradio主题对象
    """
    try:
        return gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="purple",
            neutral_hue="slate"
        )
    except AttributeError:
        return None


def get_light_theme():
    """
    获取亮色主题
    
    Returns:
        gr.Theme: Gradio主题对象
    """
    try:
        return gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="blue",
            neutral_hue="zinc"
        )
    except AttributeError:
        return None


def get_theme_by_name(theme_name: str):
    """
    根据名称获取主题
    
    Args:
        theme_name: 主题名称
        
    Returns:
        gr.Theme: Gradio主题对象
    """
    theme_map = {
        "默认": get_default_theme(),
        "暗色": get_dark_theme(),
        "亮色": get_light_theme()
    }
    
    return theme_map.get(theme_name, get_default_theme()) 