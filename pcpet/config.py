"""全局配置：模型端点、密钥、文件管理根目录等。
所有敏感值也支持用环境变量覆盖：
  PCPET_BASE_URL / PCPET_API_KEY / PCPET_MODEL / PCPET_FILES_DIR
"""
import os
from pathlib import Path

# 从本地 .env（不入库）加载敏感配置，避免密码硬编码进代码仓库
try:
    from dotenv import load_dotenv

    _PROJ_ROOT = Path(__file__).resolve().parent.parent  # 项目根目录
    load_dotenv(_PROJ_ROOT / ".env")
    load_dotenv()  # 同时保留当前工作目录的 .env
except Exception:
    pass

# ---- 对话模型（OpenAI 兼容端点） ----
BASE_URL = os.getenv("PCPET_BASE_URL", "http://172.168.100.146:5000/v1")
API_KEY = os.getenv("PCPET_API_KEY", "")   # 密钥从环境变量或 .env 读取，不入库
MODEL = os.getenv("PCPET_MODEL", "smbs/LLM-284B-MXFP4")

# ---- 文件管理工具的“势力范围” ----
# 默认为整个系统盘根目录（Windows 下如 C:\），即 AI 可读写全盘文件。
# 仍可通过 PCPET_FILES_DIR 环境变量收窄到指定目录。
FILES_DIR = os.getenv(
    "PCPET_FILES_DIR",
    os.path.abspath(os.sep),
)

# 允许 FileTools 执行“删除文件”吗？默认关（安全）。按需打开。
ENABLE_DELETE = os.getenv("PCPET_ENABLE_DELETE", "0") == "1"

# ---- 桌宠外观 ----
PET_NAME = "小电"          # 桌宠名字
WINDOW_WIDTH = 260        # 桌宠窗口宽度
WINDOW_HEIGHT = 260       # 桌宠窗口高度
CHAT_WIDTH = 380          # 对话面板宽度

def ensure_dirs():
    os.makedirs(FILES_DIR, exist_ok=True)
