"""电脑管家 Agent：基于 agno 框架。
组合 全盘文件管理工具（可访问所有盘符）+ 自定义系统监控工具，面向桌宠对话。
"""
from __future__ import annotations

from .config import (
    BASE_URL, API_KEY, MODEL, PET_NAME, ensure_dirs,
)
from .system_tools import SYSTEM_TOOLS
from .full_file_tools import FULL_FILE_TOOLS


def create_agent():
    """构建并返回单例化配置的 agno Agent（保留会话记忆）。"""
    ensure_dirs()

    from agno.agent import Agent
    from agno.models.openai import OpenAIChat

    # ---- 模型（OpenAI 兼容端点） ----
    model = OpenAIChat(
        id=MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    agent = Agent(
        name=PET_NAME,
        model=model,
        tools=FULL_FILE_TOOLS + SYSTEM_TOOLS,
        instructions=[
            f"你是「{PET_NAME}」，一个住在用户 Windows 桌面上的可爱电脑管家桌宠。",
            "性格亲切、活泼、口语化，用中文回复，适当用 emoji，回答简洁不要长篇大论。",
            "你是电脑管家：用户问电脑相关问题（CPU/内存/磁盘/进程/电池/网络/开机时长/体检）时，"
            "调用对应的系统监控工具获取真实数据，再整理成通俗易懂的回答。",
            "你也是全盘文件管家：可以在本机所有盘符（C: D: E: 等任何磁盘）读写、列出、搜索文件。"
            "只要给完整绝对路径（如 C:\\xxx\\a.txt），就能操作任意位置；"
            "用户没给路径时，优先在当前用户桌面/文档等常见位置处理。",
            "涉及删除文件、清理垃圾、覆盖修改重要文件等破坏性操作前，必须先向用户确认，得到同意再执行。",
        ],
        add_datetime_to_context=True,
        markdown=False,   # 桌宠气泡用流式文本 + 界面 Markdown 渲染
    )
    return agent
