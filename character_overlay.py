import sys
import random
import queue
from PyQt6 import QtCore, QtGui, QtWidgets

# Click-through on Windows
import win32con
import win32gui


class CharacterOverlay(QtWidgets.QWidget):
    def __init__(self, png_path: str, size_px: int = 260, margin_px: int = 18):
        super().__init__()
        self.png_path = png_path
        self.size_px = size_px
        self.margin_px = margin_px

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool  # no taskbar icon
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Image label
        self.label = QtWidgets.QLabel(self)
        self.label.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True
        )

        pix = QtGui.QPixmap(self.png_path)
        if pix.isNull():
            raise FileNotFoundError(f"Could not load PNG: {self.png_path}")

        pix = pix.scaled(
            self.size_px,
            self.size_px,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        self.label.setPixmap(pix)
        self.label.adjustSize()

        # Window size = image size
        self.resize(self.label.size())

        # Shake state
        self.base_pos = None
        self.strength = 0.0
        self.smoothed = 0.0

        # Timer for shake animation
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(16)  # ~60 fps
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self._position_bottom_right()
        self.hide()

    def show_overlay(self):
        self._position_bottom_right()
        self.show()
        self.raise_()

    def hide_overlay(self):
        self.hide()

    def set_strength(self, value: float):
        # value expected 0..1
        self.strength = max(0.0, min(1.0, float(value)))
        if not self.isVisible() and self.strength > 0.02:
            self.show_overlay()

    def _position_bottom_right(self):
        screen = QtWidgets.QApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + geo.width() - self.width() - self.margin_px
        y = geo.y() + geo.height() - self.height() - self.margin_px
        self.move(x, y)
        self.base_pos = QtCore.QPoint(x, y)

    def _make_clickthrough(self):
        hwnd = int(self.winId())
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= (
            win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST
        )
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure click-through after window exists
        self._make_clickthrough()

    def _tick(self):
        if self.base_pos is None:
            return

        # Smooth so it looks nicer
        self.smoothed = 0.85 * self.smoothed + 0.15 * self.strength

        # If effectively silent, snap back and optionally hide
        if self.smoothed < 0.01:
            self.move(self.base_pos)
            # hide when silent (optional). You can also control explicitly from your TTS loop.
            return

        # Convert strength -> pixels of shake
        max_shake_px = 18  # tune this
        shake = self.smoothed * max_shake_px

        dx = int(random.uniform(-shake, shake))
        dy = int(random.uniform(-shake, shake))

        self.move(self.base_pos.x() + dx, self.base_pos.y() + dy)


def run_overlay(
    png_path: str,
    strength_queue: "queue.Queue[float]",
    control_queue: "queue.Queue[str]",
):
    """
    Runs the Qt event loop and updates strength from queues.
    control_queue supports: "show", "hide", "quit"
    """
    app = QtWidgets.QApplication(sys.argv)
    overlay = CharacterOverlay(png_path)

    timer = QtCore.QTimer()
    timer.setInterval(16)

    def pump():
        # Control messages

        while True:
            try:
                cmd = control_queue.get_nowait()
            except Exception:
                break

            if cmd == "show":
                overlay.show_overlay()
            elif cmd == "hide":
                overlay.hide_overlay()
            elif cmd == "quit":
                overlay.hide_overlay()
                app.quit()
                return

        # Strength updates
        latest = None
        while True:
            try:
                latest = strength_queue.get_nowait()
            except Exception:
                break
        if latest is not None:
            overlay.set_strength(latest)

    timer.timeout.connect(pump)
    timer.start()

    sys.exit(app.exec())
