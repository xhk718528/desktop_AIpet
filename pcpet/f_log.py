"""崩溃捕获与日志：任何未捕获异常/段错误都写入 pet.log，且尽量不让程序闪退。"""
from __future__ import annotations

import os
import sys
import faulthandler
import logging
import traceback
from io import StringIO

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "pet.log")

_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def setup() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger("pcpet")
    if root.handlers:            # 避免重复配置
        return
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(_format)
    root.setLevel(logging.INFO)
    root.addHandler(fh)

    # 若有控制台同步打印（pythonw 下 sys.stderr 为 None，需保护）
    try:
        if sys.stderr is not None:
            sh = logging.StreamHandler(sys.stderr)
            sh.setFormatter(_format)
            root.addHandler(sh)
    except Exception:
        pass

    # 1) Python 未捕获异常：写日志，并阻止 PyQt 默认的“槽异常→退出”
    def excepthook(etype, value, tb):
        try:
            root.critical("UNCAUGHT EXCEPTION\n" + "".join(traceback.format_exception(etype, value, tb)))
        except Exception:
            pass
        try:
            print(file=sys.__stderr__)
            traceback.print_exception(etype, value, tb)
        except Exception:
            pass

    sys.excepthook = excepthook

    # 2) 无法抛出的异常（如 __del__ 里）
    def unraisablehook(args):
        try:
            root.warning("UNRAISABLE %r", args.exc_value)
        except Exception:
            pass
    try:
        sys.unraisablehook = unraisablehook
    except Exception:
        pass

    # 3) 段错误 / 解释器崩溃：faulthandler 把栈写到日志
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            faulthandler.enable(file=f)
    except Exception:
        try:
            faulthandler.enable()
        except Exception:
            pass

    root.info("=== 电脑管家桌宠启动 ===")


def log(level: int, msg: str) -> None:
    logging.getLogger("pcpet").log(level, msg)


def error(msg: str, exc: BaseException | None = None) -> None:
    if exc is not None:
        logging.getLogger("pcpet").error("%s: %s", msg, exc)
    else:
        logging.getLogger("pcpet").error(msg)


def safe(fn, label: str = "callback"):
    """包裹信号槽，防止槽内异常导致 PyQt 终止应用。"""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:  # noqa: BLE001
            logging.getLogger("pcpet").error(
                "slot %s failed: %s\n%s", label, e, traceback.format_exc()
            )
            return None
    return wrapper
