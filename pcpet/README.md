# 电脑管家桌宠「小电」🐱💻

一个基于 **agno 框架** 的桌面智能体，外观是一个会眨眼、会动的卡通桌宠，
你可以随时和它对话——它是你的**电脑管家**：帮你体检电脑、查看 CPU/内存/磁盘，
还能在专属文件夹里进行**文件管理**（读写、列出、搜索）。

## 功能
- 🖥️ **系统监控**：CPU / 内存 / 磁盘 / 进程 / 电池 / 网络 / 开机时长（只读，安全）
- 📁 **文件管理**：**全盘**文件管理（所有盘符），基于 agno `@tool` 自定义工具读写/列出/搜索任意绝对路径
- 💬 **流式对话**：打字即回的聊天面板，桌宠会“思考”“说话”，AI 回复 Markdown + 流式渲染
- 🧠 **记忆**：短期记忆（本会话历史）+ 长期记忆（跨会话记住用户偏好），agno 官方方法 + SQLite（`pcpet/memory/`）
- 🎀 **互动桌宠**：透明无边框置顶小窗，可拖动、眨眼、摇尾巴
- 🔒 **安全**：删除文件功能默认关闭（需 `PCPET_ENABLE_DELETE=1`），破坏性操作先征得确认

## 安装
```bat
:: 已包含在 venv（Python 3.11 虚拟环境）内，一般无需重复
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 运行
双击 `run_pet.bat`，或：
```bat
venv\Scripts\python.exe -m pcpet.main
```
桌宠出现在屏幕右下角：
- **单击**桌宠 → 打开/收起对话面板
- **按住拖动** → 移动桌宠（对话面板跟随）
- **右键** → 置顶 / 复位 / 退出

## 对话示例
- “帮我做个电脑体检”
- “现在内存占用多少，卡不卡？”
- “把下面的内容保存成 notes.txt：……”（会写入 `files/notes.txt`）
- “列出 files 目录里都有什么文件”

## 配置（config.py 或环境变量）
| 变量 | 默认值 | 说明 |
|---|---|---|
| `PCPET_BASE_URL` | `http://172.168.100.146:5000/v1` | 模型端点 |
| `PCPET_API_KEY` | `sk-…` | API 密钥 |
| `PCPET_MODEL` | `smbs/LLM-284B-MXFP4` | 模型名 |
| `PCPET_ENABLE_DELETE` | `0` | 设为 `1` 才允许删除文件 |

> 文件管理默认可访问**所有盘符**（全盘绝对路径）。如想收窄，可把
> `pcpet/full_file_tools.py` 里的工具按需移除即可。

## 运行时崩溃排查
- 程序自带崩溃捕获：任何异常（包括信号槽异常、段错误）都会写入 `pcpet/logs/pet.log`，
  且**不会因为某个回调出错就让整个程序闪退**。
- 若还出问题，用 `run_pet_debug.bat`（带控制台）运行，报错会直接显示；或打开
  `pcpet/logs/pet.log` 查看最新记录。

## 目录结构
```
pcpet/
├── main.py            # 入口
├── config.py          # 配置
├── agent_core.py      # agno Agent（全盘文件工具 + 系统工具）
├── full_file_tools.py # 全盘文件管理工具（@tool）
├── system_tools.py    # psutil 系统监控工具
├── pet.py             # 桌宠 & 对话面板 GUI
└── requirements.txt
```
