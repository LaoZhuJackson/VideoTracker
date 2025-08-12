import sys
import ctypes
from ctypes import wintypes
import win32con
import win32api
import win32gui

WM_HOTKEY = 0x0312
# 定义快捷键ID
PLAY_PAUSE_ID = 1
FORWARD_ID = 2
BACKWARD_ID = 3
FULLSCREEN_ID = 4
VOLUME_UP_ID = 5
VOLUME_DOWN_ID = 6


class HotkeyManager:
    def __init__(self):
        # 注册系统级全局快捷键
        if sys.platform == "win32":
            self._register_global_hotkeys()

    def _register_global_hotkeys(self):
        """注册系统级全局快捷键（仅Windows）"""
        try:
            # 播放/暂停: Ctrl+Alt+P
            win32api.RegisterHotKey(
                int(self.winId()), PLAY_PAUSE_ID,
                win32con.MOD_CONTROL | win32con.MOD_ALT,
                win32con.VK_P
            )

            # 快进: Ctrl+Alt+Right
            win32api.RegisterHotKey(
                int(self.winId()), FORWARD_ID,
                win32con.MOD_CONTROL | win32con.MOD_ALT,
                win32con.VK_RIGHT
            )

            # 快退: Ctrl+Alt+Left
            win32api.RegisterHotKey(
                int(self.winId()), BACKWARD_ID,
                win32con.MOD_CONTROL | win32con.MOD_ALT,
                win32con.VK_LEFT
            )

            # 全屏: Ctrl+Alt+F
            win32api.RegisterHotKey(
                int(self.winId()), FULLSCREEN_ID,
                win32con.MOD_CONTROL | win32con.MOD_ALT,
                win32con.VK_F
            )
        except Exception as e:
            print(f"Failed to register hotkeys: {e}")
