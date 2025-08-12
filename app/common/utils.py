import platform
import ctypes
from ctypes import wintypes

import win32gui
import win32con

# Win32 常量
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_EX_NOACTIVATE = 0x08000000

WS_EX_APPWINDOW = 0x00040000
GWL_EXSTYLE = -20

user32 = ctypes.WinDLL("user32", use_last_error=True)

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowW.restype = wintypes.HWND

SetParent = user32.SetParent
SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
SetParent.restype = wintypes.HWND

SetWindowLongW = user32.SetWindowLongW
SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
SetWindowLongW.restype = ctypes.c_long

GetWindowLongW = user32.GetWindowLongW
GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
GetWindowLongW.restype = ctypes.c_long

SetWindowPos = user32.SetWindowPos
SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         ctypes.c_uint]
SetWindowPos.restype = wintypes.BOOL

IsWindow = user32.IsWindow
IsWindow.argtypes = [wintypes.HWND]
IsWindow.restype = wintypes.BOOL


def translate_to_specific_window(hwnd, target_hwnd):
    # 将焦点转移到另一个窗口（例如父窗口）
    user32.SetFocus(target_hwnd)

    # 设置Z序确保焦点转移成功
    user32.SetWindowPos(
        hwnd,
        target_hwnd,  # 放在目标窗口下方
        0, 0, 0, 0,
        0x0001 | 0x0002 | 0x0010  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    )


def set_focus_state(hwnd, focus: bool):
    """控制窗口的焦点状态"""
    if not hwnd or not IsWindow(hwnd):
        return
    print(f"Setting webview focus state: {'Enabled' if focus else 'Disabled'}")

    if focus:
        # 允许获取焦点
        ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_ex_style = ex_style & ~WS_EX_NOACTIVATE
        SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex_style)
        user32.SetFocus(hwnd)
    else:
        # 禁止获取焦点
        ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_ex_style = ex_style | WS_EX_NOACTIVATE
        SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex_style)
        user32.SetActiveWindow(0)
        user32.SetFocus(0)
