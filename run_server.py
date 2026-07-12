"""
开发服务器启动脚本
使用方式：python run_server.py
"""
import sys
import os

# 确保项目根目录和 backend 目录都在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend"))

import uvicorn
uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
