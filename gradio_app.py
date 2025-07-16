#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gradio应用独立启动入口
这个文件用于直接启动Gradio界面，不经过FastAPI
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到系统路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入Gradio应用
from app.ui.app import create_gradio_app

if __name__ == "__main__":
    # 创建并启动Gradio应用
    demo = create_gradio_app()
    
    # 设置启动参数
    port = int(os.getenv("GRADIO_PORT", 7860))
    share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
    
    # 启动应用
    demo.launch(
        server_name="localhost",
        server_port=port,
        share=share,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        auth=None,  # 可以在这里设置认证
    ) 