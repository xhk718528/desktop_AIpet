"""电脑管家桌宠 - 程序入口。
用法:  python main.py    （发布时可用 pythonw main.py 不弹控制台）
"""
from __future__ import annotations

import sys
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

from . import config
from . import pet as petmod
from . import f_log


class ChatWorker(QThread):
    """后台线程运行 agno Agent，流式产出回复，避免卡住 GUI。"""
    partial = pyqtSignal(str)
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, agent, message, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.message = message

    def run(self):
        text = ""
        # 记忆身份：短期记忆按 session_id，长期记忆按 user_id（影响 SQLite 存取）
        run_kwargs = dict(user_id=config.USER_ID, session_id=config.get_session_id())
        try:
            # 优先流式：agno 3.x 文本增量事件为 RunContent
            try:
                for chunk in self.agent.run(self.message, stream=True, **run_kwargs):
                    ev = getattr(chunk, "event", None)
                    content = getattr(chunk, "content", None)
                    if ev == "RunContent" and isinstance(content, str) and content:
                        text += content
                        self.partial.emit(content)
            except TypeError:
                pass
            # 若流式没拿到任何文本（接口差异/空回复），降级为非流式一次
            if not text:
                resp = self.agent.run(self.message, **run_kwargs)
                text = getattr(resp, "content", "") or ""
                if text:
                    self.partial.emit(text)
            self.done.emit(text)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class DesktopPet:
    def __init__(self, app: QApplication):
        self.app = app
        from .agent_core import create_agent
        self.agent = create_agent()

        self.pet_win = petmod.PetWindow(self._toggle_chat, self._on_pet_move)
        self.chat = petmod.ChatWindow(self._on_send)
        self.chat.hide()

        self._place()
        self.pet_win.show()
        self.worker = None

    def _place(self):
        wa = self.app.primaryScreen().availableGeometry()
        pet_x = wa.right() - self.pet_win.width() - 60
        pet_y = wa.bottom() - self.pet_win.height() - 40
        self.pet_win.move(pet_x, pet_y)
        self._sync_chat()

    def _on_pet_move(self, pos):
        if pos is None:          # 复位到默认位置
            self._place()
        else:
            self._sync_chat()

    def _sync_chat(self):
        p = self.pet_win.pos()
        self.chat.move(p.x() - self.chat.width() - 14,
                       p.y() + self.pet_win.height() - self.chat.height())

    @f_log.safe
    def _toggle_chat(self):
        if self.chat.isVisible():
            self.chat.hide()
            self.pet_win.set_think(False)
        else:
            self.chat.show()
            self.chat.raise_()

    def _on_send(self, text: str):
        if self.worker and self.worker.isRunning():
            return
        self.worker = ChatWorker(self.agent, text)
        self.worker.partial.connect(f_log.safe(self._on_partial, "_on_partial"))
        self.worker.done.connect(f_log.safe(self._on_done, "_on_done"))
        self.worker.failed.connect(f_log.safe(self._on_failed, "_on_failed"))
        self.pet_win.set_think(True, "让我看看…")
        self.chat.set_thinking()
        self.worker.start()

    def _on_partial(self, delta: str):
        self.pet_win.set_talking(True)
        self.pet_win.set_think(False)
        self.chat.add_assistant_delta(delta)

    def _on_done(self, _full: str):
        self.chat.finish_assistant()
        self.pet_win.set_talking(False)
        self.pet_win.set_think(False)

    def _on_failed(self, err: str):
        self.chat.finish_assistant()
        self.pet_win.set_talking(False)
        self.pet_win.set_think(False)
        self.chat.add_error(err)


def run():
    try:
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    config.ensure_dirs()
    f_log.setup()
    app = QApplication(sys.argv)
    DesktopPet(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
