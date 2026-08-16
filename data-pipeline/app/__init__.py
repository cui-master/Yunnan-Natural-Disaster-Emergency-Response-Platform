"""data-pipeline 应用包

在 import 时自动加载 .env 文件，确保 os.getenv 能读到配置值。
必须在任何 os.getenv 调用之前完成（本文件在 from app.xxx import 时最先执行）。
"""
from dotenv import load_dotenv

load_dotenv()
