"""桌宠图形界面：PyQt5 透明无边框的卡通桌宠 + 可唤出的对话面板 + 流式回复线程。
不依赖 agno 具体接口，便于单独调试。
"""
from __future__ import annotations

import math
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QLinearGradient, QRadialGradient, QFont,
    QPolygonF, QPainterPath, QPen, QFontMetrics,
)
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QTextBrowser,
    QPushButton, QMenu, QApplication, QLabel, QGraphicsDropShadowEffect,
    QScrollArea,
)

from . import config
from . import f_log


# ---------------------------------------------------------------- 画桌宠
class PetWidget(QWidget):
    """用 QPainter 手绘一个圆润的机器人小猫咪“小电”。"""

    def __init__(self, size=170, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.blink = 0.0          # 0=睁眼, 1=闭眼(用于过渡)
        self.talking = False      # 说话时嘴巴开合
        self.think = False        # 思考时头顶冒气泡
        self._frame = 0
        self._blink_timer = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(70)      # ~14fps，够用

    def _tick(self):
        self._frame += 1
        # 随机眨眼
        self._blink_timer += 1
        if self._blink_timer > 90:
            self.blink = 1.0
            if self._blink_timer > 96:
                self._blink_timer = 0
                self.blink = 0.0
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size
        bob = math.sin(self._frame * 0.28) * 3   # 待机时轻微上下浮动

        cx, cy = s // 2, s // 2 + int(bob) + 6
        R = s // 2 - 12

        # 尾巴(右侧，会摆动)
        p.save()
        p.translate(cx + R * 0.55, cy + R * 0.35)
        p.rotate(30 + math.sin(self._frame * 0.3) * 25)
        tail = QPainterPath()
        tail.moveTo(0, 0)
        tail.cubicTo(R * 0.45, -R * 0.35, R * 0.5, -R * 0.62, R * 0.22, -R * 0.78)
        pen = QPen(QColor(96, 165, 250), 9, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawPath(tail)
        p.restore()

        # 耳朵(两枚三角)
        ear = QPolygonF([
            QPointF(cx - R * 0.52, cy - R * 0.52),
            QPointF(cx - R * 0.34, cy - R * 1.02),
            QPointF(cx - R * 0.10, cy - R * 0.62),
        ])
        ear2 = QPolygonF([
            QPointF(cx + R * 0.52, cy - R * 0.52),
            QPointF(cx + R * 0.34, cy - R * 1.02),
            QPointF(cx + R * 0.10, cy - R * 0.62),
        ])
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(88, 166, 252))
        p.drawPolygon(ear)
        p.drawPolygon(ear2)
        # 耳内粉色
        p.setBrush(QColor(255, 190, 205))
        p.drawEllipse(QRectF(cx - R * 0.42, cy - R * 0.78, R * 0.20, R * 0.26))
        p.drawEllipse(QRectF(cx + R * 0.22, cy - R * 0.78, R * 0.20, R * 0.26))

        # 天线
        pen = QPen(QColor(110, 120, 160), 3, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(cx, cy - R * 0.92), QPointF(cx, cy - R * 1.18))
        glow = QRadialGradient(QPointF(cx, cy - R * 1.22), 8)
        glow.setColorAt(0, QColor(120, 230, 255))
        glow.setColorAt(1, QColor(50, 160, 255, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx - 7, cy - R * 1.22 - 7, 14, 14))

        # 身体(圆润的主椭圆)
        grad = QLinearGradient(cx, cy - R, cx, cy + R)
        grad.setColorAt(0, QColor(150, 205, 255))
        grad.setColorAt(1, QColor(96, 168, 250))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(70, 130, 210), 2))
        p.drawEllipse(QRectF(cx - R, cy - R, 2 * R, 2 * R))

        # 肚皮浅色斑
        belly = QPainterPath()
        belly.moveTo(cx - R * 0.45, cy - R * 0.15)
        belly.quadTo(cx, cy + R * 0.55, cx + R * 0.45, cy - R * 0.15)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(225, 240, 255, 200))
        p.drawPath(belly)

        # 腮红
        p.setBrush(QColor(255, 150, 170, 210))
        p.drawEllipse(QRectF(cx - R * 0.68, cy + R * 0.10, R * 0.20, R * 0.14))
        p.drawEllipse(QRectF(cx + R * 0.48, cy + R * 0.10, R * 0.20, R * 0.14))

        # 眼睛
        eyeL = QRectF(cx - R * 0.42, cy - R * 0.22, R * 0.26, R * 0.22)
        eyeR = QRectF(cx + R * 0.16, cy - R * 0.22, R * 0.26, R * 0.22)
        if self.talking or self.think:
            # 认真/说话时眯成弯月眼
            p.setPen(QPen(QColor(40, 60, 90), 3, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawArc(eyeL, 0, 180 * 16)
            p.drawArc(eyeR, 0, 180 * 16)
        elif self.blink >= 1:
            p.setPen(QPen(QColor(40, 60, 90), 2.6, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(eyeL.left(), eyeL.center().y()), QPointF(eyeL.right(), eyeL.center().y()))
            p.drawLine(QPointF(eyeR.left(), eyeR.center().y()), QPointF(eyeR.right(), eyeR.center().y()))
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(40, 60, 90))
            p.drawEllipse(eyeL)
            p.drawEllipse(eyeR)
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(eyeL.left() + eyeL.width() * 0.28, eyeL.top() + 2, 4, 4))

        # 嘴巴
        if self.talking:
            # 说话：嘴巴开合
            open_h = 4 + int(abs(math.sin(self._frame * 0.9))) * 3
            p.setBrush(QColor(190, 90, 110))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(cx - 6, cy + R * 0.10, 12, open_h))
        else:
            p.setPen(QPen(QColor(70, 90, 120), 2.2, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(cx - 9, cy - R * 0.04, 18, 12), 200 * 16, 140 * 16)

        p.end()


# ---------------------------------------------------------------- 情绪气泡
class ThinkBubble(QWidget):
    """说话/思考时显示在宠物头顶的圆角气泡(使用了富文本)。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_text(self, t: str):
        self._text = t
        w = len(t) * 14 + 34
        self.setFixedWidth(w)
        self.adjustSize()
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -10)
        p.setPen(QPen(QColor(255, 255, 255, 90), 1))
        p.setBrush(QColor(255, 255, 255, 235))
        p.drawRoundedRect(r, 10, 10)
        # 小尾巴
        tail = QPolygonF([QPointF(r.center().x() - 6, r.bottom()),
                          QPointF(r.center().x() + 6, r.bottom()),
                          QPointF(r.center().x(), r.bottom() + 9)])
        p.drawPolygon(tail)
        p.setPen(QColor(60, 80, 110))
        f = QFont("Microsoft YaHei UI", 10)
        p.setFont(f)
        p.drawText(r.adjusted(6, 0, -6, 0), Qt.AlignCenter, self._text)
        p.end()


# ---------------------------------------------------------------- 气泡样式
_BOT_CSS = (
    "QTextBrowser{background:#f2f6fd;color:#1f2937;"
    "border:1px solid #e7edf7;border-radius:14px;}"
)
_MD_DOC_CSS = (
    "h1,h2,h3{color:#2563eb;}"
    "code{background:#eaf0fa;color:#b45309;}"
    "pre{background:#1e2a3a;color:#e2e8f0;border-radius:8px;padding:6px;}"
    "pre code{background:none;color:#e2e8f0;}"
    "blockquote{color:#5b6477;border-left:3px solid #3b82f6;}"
    "table{border-collapse:collapse;} th,td{border:1px solid #d8e0ee;padding:4px 8px;} th{background:#eef2f8;}"
    "a{color:#2563eb;}"
)


class _Bubble(QWidget):
    """单条消息气泡：横向布局，向左或向右对齐。"""

    def __init__(self, side: str, control: QWidget, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        if side == "right":
            lay.addStretch(1)
            lay.addWidget(control, 0, Qt.AlignTop)
        else:
            lay.addWidget(control, 0, Qt.AlignTop)
            lay.addStretch(1)


# ---------------------------------------------------------------- 对话面板
class ChatWindow(QWidget):
    """可拖动的半透明对话窗口：左右气泡 + AI 回复渲染 Markdown（控件实现）。"""

    _MAX_BUBBLE = 0.80

    def __init__(self, on_send, parent=None):
        super().__init__(parent)
        self.on_send = on_send
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(390, 480)

        self._drag = None
        self._dragging = False
        self.messages = []                 # 每项: {"role","text","kind"}
        self._stream_box = None            # 当前 AI 流式气泡的 QTextBrowser
        self._stream_text = ""             # 当前 AI 累积文本
        self._controls = []                # 所有气泡控件，用于统一刷新宽度
        self._render_timer = QTimer(self)  # 周期性渲染流式文本（约 25fps）
        self._render_timer.setInterval(40)
        self._render_timer.timeout.connect(self._flush_stream)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 14)

        card = QFrame(self)
        card.setObjectName("card")
        card.setStyleSheet(
            "QFrame#card{background:#ffffff;"
            "border:1px solid #e3e8f2;border-radius:18px;}"
        )
        sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(34); sh.setOffset(0, 6); sh.setColor(QColor(0, 0, 0, 150))
        card.setGraphicsEffect(sh)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(8)

        # ---- 标题栏 ----
        head = QHBoxLayout(); head.setSpacing(9)
        avatar = QLabel("⚡")
        avatar.setFixedSize(30, 30); avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #3b82f6,stop:1 #22d3ee);"
            "border-radius:15px;color:#fff;font-size:16px;"
        )
        tcol = QVBoxLayout(); tcol.setSpacing(1)
        tt = QLabel(f"{config.PET_NAME} · 电脑管家")
        tt.setStyleSheet("color:#1f2937;font-size:14px;font-weight:600;")
        ts = QLabel("● 在线 · 随时帮你")
        ts.setStyleSheet("color:#16a34a;font-size:11px;")
        tcol.addWidget(tt); tcol.addWidget(ts)
        head.addWidget(avatar); head.addLayout(tcol); head.addStretch(1)
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet(
            "QPushButton{background:transparent;color:#8a94a6;border:none;border-radius:12px;font-size:13px;}"
            "QPushButton:hover{background:#eef2f8;color:#333;}"
        )
        self.btn_close.clicked.connect(self.hide)
        head.addWidget(self.btn_close)
        cl.addLayout(head)

        # ---- 消息区：可滚动容器 ----
        self.scroll = QScrollArea(card)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:transparent;width:6px;margin:2px;}"
            "QScrollBar::handle:vertical{background:#c8d2e4;border-radius:3px;min-height:24px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:transparent;}"
        )
        self.scroll.setViewportMargins(2, 2, 2, 2)
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        self.mbox = QVBoxLayout(body)
        self.mbox.setContentsMargins(2, 4, 2, 4)
        self.mbox.setSpacing(10)
        self.mbox.addStretch(1)          # 消息从顶部排，底部留弹性空间
        self.scroll.setWidget(body)
        cl.addWidget(self.scroll, 1)

        # ---- 输入行 ----
        self.input = QLineEdit(card)
        self.input.setPlaceholderText(f"和{config.PET_NAME}说点什么…（回车发送）")
        self.input.setStyleSheet(
            "QLineEdit{background:#f7f9fc;color:#1f2937;"
            "border:1px solid #d7deeb;border-radius:12px;padding:9px 12px;font-size:13px;}"
            "QLineEdit:focus{border:1px solid #3b82f6;background:#fff;}"
        )
        self.input.returnPressed.connect(self._send)
        self.btn = QPushButton("发送")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3b82f6,stop:1 #2563eb);"
            "color:#fff;border:none;border-radius:12px;padding:9px 16px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#2f6fe0;}QPushButton:pressed{background:#1f54c0;}"
        )
        self.btn.clicked.connect(self._send)
        row = QHBoxLayout(); row.setSpacing(8)
        row.addWidget(self.input, 1); row.addWidget(self.btn)
        cl.addLayout(row)

        outer.addWidget(card)

        # 欢迎语
        self.add_assistant(
            "你好！我是" + config.PET_NAME
            + "，你的**电脑管家桌宠**~ 可以问我\n\n- `电脑体检`\n- 内存 / CPU / 磁盘占用\n"
            + "- 帮我整理文件 📁\n\n需要时我也会**调用系统工具**给你真实数据 😊"
        )

    # ---------- 气泡构建 ----------
    def _max_w(self) -> int:
        return max(170, int(self.scroll.viewport().width() * ChatWindow._MAX_BUBBLE))

    def _user_bubble(self, text: str) -> _Bubble:
        lbl = QLabel(text)
        lbl.setTextFormat(Qt.PlainText)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setMaximumWidth(self._max_w())
        lbl.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #3b82f6,stop:1 #2563eb);"
            "color:#fff;border-radius:14px;border-top-right-radius:4px;padding:8px 12px;font-size:13.5px;"
        )
        self._controls.append(lbl)
        return _Bubble("right", lbl)

    def _bot_browser(self, text: str, thinking=False) -> QTextBrowser:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(True)
        tb.setFrameShape(QFrame.NoFrame)
        tb.setStyleSheet(_BOT_CSS)
        tb.document().setDefaultStyleSheet(_MD_DOC_CSS)
        tb.document().setDocumentMargin(10)
        tb.setMaximumWidth(self._max_w())
        tb.setMinimumWidth(60)
        tb.setTextInteractionFlags(tb.textInteractionFlags() | Qt.TextSelectableByMouse)
        if thinking:
            tb.setHtml('<span style="color:#8b96ab">正在思考…</span>')
        else:
            tb.setMarkdown(text or "…")
        self._controls.append(tb)
        return tb

    def _new_bot(self, text: str, kind="normal", stream=False):
        self.messages.append({"role": "bot", "text": text, "kind": kind})
        tb = self._bot_browser(text, thinking=(kind == "thinking"))
        self.mbox.insertWidget(self.mbox.count() - 1, _Bubble("left", tb))
        if stream:
            self._stream_box = tb
            self._stream_text = text
        self._scroll_bottom()

    def _scroll_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _refresh_widths(self):
        """窗口尺寸定下来后，统一刷新所有气泡的宽度上限，避免早期创建的气泡偏窄。"""
        mw = self._max_w()
        for c in self._controls:
            try:
                c.setMaximumWidth(mw)
            except Exception:
                pass

    def showEvent(self, e):
        super().showEvent(e)
        self._refresh_widths()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._refresh_widths()

    def _flush_stream(self):
        # 周期回调：把当前累积的流式文本渲染进 AI 气泡（不停止定时器）
        if self._stream_box is not None:
            self._stream_box.setMarkdown(self._stream_text or "…")
            if self.messages and self.messages[-1]["role"] == "bot":
                self.messages[-1]["kind"] = "normal"
                self.messages[-1]["text"] = self._stream_text
            self._scroll_bottom()

    def _stop_stream(self):
        if self._render_timer.isActive():
            self._render_timer.stop()
        if self._stream_box is not None:
            self._stream_box.setMarkdown(self._stream_text or "（暂无内容）")
            if self.messages and self.messages[-1]["role"] == "bot":
                self.messages[-1]["kind"] = "normal"
                self.messages[-1]["text"] = self._stream_text
        self._stream_box = None
        self._stream_text = ""

    # ---------- 对外接口 ----------
    @f_log.safe
    def _send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self._stop_stream()
        self.messages.append({"role": "user", "text": text, "kind": "normal"})
        self.mbox.insertWidget(self.mbox.count() - 1, self._user_bubble(text))
        self._scroll_bottom()
        self.on_send(text)

    @f_log.safe
    def set_thinking(self):
        self._new_bot("", "thinking", stream=True)

    @f_log.safe
    def add_assistant(self, text: str, kind="normal"):
        self._new_bot(text, kind, stream=False)

    @f_log.safe
    def add_assistant_delta(self, delta: str):
        if self._stream_box is None:
            self._new_bot("", "normal", stream=True)
        self._stream_text += delta
        if not self._render_timer.isActive():
            self._render_timer.start()   # 周期刷新（每 40ms），流式期间持续渲染

    @f_log.safe
    def finish_assistant(self):
        self._stop_stream()
        self._scroll_bottom()

    @f_log.safe
    def add_error(self, err: str):
        self._stop_stream()
        self._new_bot("**⚠️ 出错了**\n\n" + err, "error", stream=False)

    # --- 拖动 ---
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPos() - self.frameGeometry().topLeft()
            self._dragging = True

    def mouseMoveEvent(self, e):
        if self._dragging and self._drag is not None:
            self.move(e.globalPos() - self._drag)

    def mouseReleaseEvent(self, e):
        self._dragging = False


# ---------------------------------------------------------------- 宠物主窗口
class PetWindow(QWidget):
    """透明、无边框、置顶的桌宠窗口，承载宠物形象与思考气泡。"""

    def __init__(self, on_toggle_chat=None, on_move=None):
        super().__init__()
        self.on_toggle_chat = on_toggle_chat
        self.on_move = on_move
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        # 竖向布局：气泡在上，宠物在下
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.bubble = ThinkBubble(self)
        self.bubble.set_text("…")
        self.bubble.adjustSize()
        self.bubble.move(10, 4)
        self.bubble.hide()

        self.pet = PetWidget(170, self)
        lay.addStretch(1)
        lay.addWidget(self.pet, 0, Qt.AlignHCenter)
        lay.addStretch(1)

        # 拖动相关
        self._press = None
        self._moved = False
        self.setMouseTracking(True)

    # --- 与控制器交互 ---
    def set_think(self, on: bool, text: str = "正在思考…"):
        if on:
            self.bubble.set_text(text)
            self.bubble.adjustSize()
            self.bubble.move(10, 4)
            self.bubble.show()
        else:
            self.bubble.hide()
        self.pet.think = on
        self.pet.update()

    def set_talking(self, on: bool):
        self.pet.talking = on
        self.pet.update()

    # --- 拖动 & 右键菜单 ---
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = e.globalPos() - self.frameGeometry().topLeft()
            self._moved = False
        elif e.button() == Qt.RightButton:
            self._menu(e.globalPos())

    def mouseMoveEvent(self, e):
        if self._press is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._press)
            self._moved = True
            if self.on_move:
                self.on_move(self.pos())

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._press is not None:
            if not self._moved and self.on_toggle_chat:
                # 单击：唤出/收起对话
                self.on_toggle_chat()
            self._press = None

    def _menu(self, gpos):
        m = QMenu(self)
        act_chat = m.addAction("💬 打开/收起对话")
        act_top = m.addAction("📌 置顶" if self.windowFlags() & Qt.WindowStaysOnTopHint else "📌 取消置顶")
        m.addSeparator()
        act_pos = m.addAction("🔄 回到右下角")
        act_quit = m.addAction("🚪 退出桌宠")
        chosen = m.exec_(gpos)
        if chosen == act_chat and self.on_toggle_chat:
            self.on_toggle_chat()
        elif chosen == act_top:
            flags = self.windowFlags() ^ Qt.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self.show()
        elif chosen == act_pos and self.on_move:
            self.on_move(None)  # None 表示复位到默认位置
        elif chosen == act_quit:
            QApplication.instance().quit()
