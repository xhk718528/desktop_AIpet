"""全盘文件管理工具：基于绝对路径，可访问本机所有盘符（C: / D: / E: …）。
使用 agno 的 @tool 装饰器定义，替换仅限单目录的内置 FileTools。
删除功能默认关闭（由 config.ENABLE_DELETE 控制）。
"""
from __future__ import annotations

import os
import fnmatch

from agno.tools import tool

from . import config


def _norm(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(str(path))))


# 搜索时跳过的系统/噪音目录，避免遍历太慢
_SKIP = {
    "$RECYCLE.BIN", "System Volume Information", "Windows", "Program Files",
    "Program Files (x86)", "ProgramData", "AppData", "node_modules",
    ".git", "__pycache__", "$Recycle.Bin", "Temp",
}
_TEXT_EXT = (".txt", ".md", ".csv", ".log", ".py", ".json", ".ini", ".cfg", ".yml", ".yaml", ".xml", ".html", ".bat", ".ps1", ".sql")


@tool(show_result=False)
def read_file(path: str, max_chars: int = 100000) -> dict:
    """读取任意盘符下指定文件的文本内容。path 必须是完整绝对路径，例如 C:\\Users\\xxx\\a.txt 或 D:\\doc\\b.md。"""
    p = _norm(path)
    if not os.path.isfile(p):
        return {"error": f"文件不存在: {p}"}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            data = f.read(max_chars)
    except Exception as e:  # noqa: BLE001
        return {"error": f"读取失败: {e}"}
    return {"path": p, "content": data}


@tool(show_result=False)
def write_file(path: str, content: str) -> dict:
    """把 content 写入任意盘符的绝对路径文件（自动创建父目录）。可覆盖已有文件。"""
    p = _norm(path)
    try:
        parent = os.path.dirname(p)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:  # noqa: BLE001
        return {"error": f"写入失败: {e}"}
    return {"saved": p, "size": os.path.getsize(p)}


@tool(show_result=False)
def list_files(path: str, max_items: int = 80) -> dict:
    """列出任意盘符下指定目录的子项（含子目录和文件）。"""
    p = _norm(path)
    if not os.path.isdir(p):
        return {"error": f"目录不存在: {p}"}
    items = []
    try:
        for name in sorted(os.listdir(p)):
            full = os.path.join(p, name)
            kinds = "dir" if os.path.isdir(full) else "file"
            items.append({"name": name, "type": kinds})
            if len(items) >= max_items:
                break
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    return {"path": p, "items": items, "count": len(items)}


@tool(show_result=False)
def search_files(root_dir: str, pattern: str, max_results: int = 25) -> dict:
    """在 root_dir（任意盘符）下按文件名通配符（如 *.pdf 或 report*）搜索文件。"""
    root = _norm(root_dir)
    if not os.path.isdir(root):
        return {"error": f"目录不存在: {root}"}
    hits = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in _SKIP]
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                hits.append(os.path.join(d, f))
                if len(hits) >= max_results:
                    return {"root": root, "matches": hits, "count": len(hits)}
    return {"root": root, "matches": hits, "count": len(hits)}


@tool(show_result=False)
def search_content(root_dir: str, query: str, max_results: int = 10) -> dict:
    """在 root_dir（任意盘符）下搜索文本内容包含 query 的文件（只扫常见文本后缀）。"""
    root = _norm(root_dir)
    if not os.path.isdir(root):
        return {"error": f"目录不存在: {root}"}
    hits = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in _SKIP]
        for f in files:
            if f.endswith(_TEXT_EXT):
                fp = os.path.join(d, f)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                        if query.lower() in fh.read().lower():
                            hits.append(fp)
                            if len(hits) >= max_results:
                                return {"root": root, "matches": hits, "count": len(hits)}
                except Exception:  # noqa: BLE001
                    continue
    return {"root": root, "matches": hits, "count": len(hits)}


@tool(show_result=False)
def delete_file(path: str) -> dict:
    """删除任意盘符下指定路径的文件。仅当 PCPET_ENABLE_DELETE=1 时生效。"""
    if not config.ENABLE_DELETE:
        return {"error": "删除功能未开启（需设置环境变量 PCPET_ENABLE_DELETE=1）。", "deleted": False}
    p = _norm(path)
    if not os.path.isfile(p):
        return {"error": f"文件不存在: {p}", "deleted": False}
    try:
        os.remove(p)
    except Exception as e:  # noqa: BLE001
        return {"error": f"删除失败: {e}", "deleted": False}
    return {"deleted": p, "deleted_ok": True}


# 全盘文件工具集合
FULL_FILE_TOOLS = [read_file, write_file, list_files, search_files, search_content, delete_file]
