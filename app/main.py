"""
FastAPI应用入口
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 导入Gradio应用
from app.ui.app import create_gradio_app
import gradio as gr

# 创建FastAPI应用
app = FastAPI(
    title="Darwin Agent",
    description="基于LangChain和LangGraph的智能代理系统",
    version="0.1.0",
)

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent
STATIC_DIR = os.path.join(ROOT_DIR, "static")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 创建Gradio应用
gradio_app = create_gradio_app()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    根路由，重定向到UI界面
    """
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Darwin Agent</title>
            <meta http-equiv="refresh" content="0;url=/ui" />
        </head>
        <body>
            <p>正在重定向到 <a href="/ui">UI界面</a>...</p>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {"status": "ok"}


# 启动应用
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )