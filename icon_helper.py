# icon_helper.py
import sys
import os
import shutil
import ctypes
import tkinter as tk
import psutil

try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", ctypes.c_void_p),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", ctypes.c_ulong),
        ("szDisplayName", ctypes.c_wchar * 260),
        ("szTypeName", ctypes.c_wchar * 80),
    ]


if sys.platform == "win32":
    try:
        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        shell32.SHGetFileInfoW.restype = ctypes.c_uintptr_t
        shell32.SHGetFileInfoW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_uint32, ctypes.POINTER(SHFILEINFO),
            ctypes.c_uint32, ctypes.c_uint32
        ]

        shell32.ExtractIconExW.restype = ctypes.c_uint
        shell32.ExtractIconExW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_uint
        ]

        user32.DestroyIcon.restype = ctypes.c_bool
        user32.DestroyIcon.argtypes = [ctypes.c_void_p]

        user32.GetDC.restype = ctypes.c_void_p
        user32.GetDC.argtypes = [ctypes.c_void_p]

        user32.ReleaseDC.restype = ctypes.c_int
        user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        user32.DrawIconEx.restype = ctypes.c_bool
        user32.DrawIconEx.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
            ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint
        ]

        gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
        gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]

        gdi32.DeleteDC.restype = ctypes.c_bool
        gdi32.DeleteDC.argtypes = [ctypes.c_void_p]

        gdi32.CreateDIBSection.restype = ctypes.c_void_p
        gdi32.CreateDIBSection.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(BITMAPINFOHEADER), ctypes.c_uint,
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_uint32
        ]

        gdi32.SelectObject.restype = ctypes.c_void_p
        gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        gdi32.DeleteObject.restype = ctypes.c_bool
        gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    except Exception:
        pass


class IconHelper:
    """应用程序图标提取与缓存助手"""

    _cache = {}
    _default_icon = None

    @classmethod
    def get_default_icon(cls):
        """生成默认应用占位图标"""
        if cls._default_icon is None:
            ppm_header = "P6 16 16 255 "
            ppm_pixels = bytearray()
            for y in range(16):
                for x in range(16):
                    if x in (0, 15) or y in (0, 15):
                        ppm_pixels.extend([100, 120, 140])
                    else:
                        ppm_pixels.extend([180, 200, 220])
            ppm_data = ppm_header.encode("ascii") + bytes(ppm_pixels)
            cls._default_icon = tk.PhotoImage(data=ppm_data)
        return cls._default_icon

    @classmethod
    def resolve_path(cls, path):
        """解析并格式化绝对路径"""
        if not path:
            return ""
        path = os.path.expandvars(path.strip('"').strip())
        if os.path.exists(path):
            return path

        if not os.path.isabs(path) or not os.path.exists(path):
            exe_name = os.path.basename(path)
            found = shutil.which(exe_name)
            if found and os.path.exists(found):
                return found

            if sys.platform == "win32":
                import winreg
                for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    app_path_key = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe_name}"
                    try:
                        with winreg.OpenKey(root_key, app_path_key) as key:
                            p_val, _ = winreg.QueryValueEx(key, "")
                            if p_val:
                                p_val = os.path.expandvars(str(p_val).strip('"').strip())
                                if os.path.exists(p_val):
                                    return p_val
                    except Exception:
                        pass

            try:
                for p in psutil.process_iter(['name', 'exe']):
                    if p.info['name'] and p.info['name'].lower() == exe_name.lower():
                        if p.info['exe'] and os.path.exists(p.info['exe']):
                            return p.info['exe']
            except Exception:
                pass
        return path

    @classmethod
    def get_icon(cls, exe_path=""):
        """获取指定 .exe 路径或进程名的 16x16 图标 PhotoImage"""
        resolved_path = cls.resolve_path(exe_path)
        key = resolved_path.lower() if resolved_path else (exe_path.lower() if exe_path else "default")

        if key in cls._cache:
            return cls._cache[key]

        icon = cls._extract_win32_icon(resolved_path if resolved_path else exe_path)
        if icon is None:
            icon = cls.get_default_icon()

        cls._cache[key] = icon
        return icon

    @classmethod
    def _extract_win32_icon(cls, exe_path):
        if sys.platform != "win32" or not HAS_PIL:
            return None

        hicon = cls._get_hicon(exe_path)
        if not hicon:
            return None

        pil_img = cls._hicon_to_pil_via_draw(hicon)
        ctypes.windll.user32.DestroyIcon(hicon)

        if pil_img:
            return ImageTk.PhotoImage(pil_img)
        return None

    @classmethod
    def _get_hicon(cls, exe_path):
        shfi = SHFILEINFO()
        SHGFI_ICON = 0x000000100
        SHGFI_SMALLICON = 0x000000001
        SHGFI_USEFILEATTRIBUTES = 0x000000010

        flags = SHGFI_ICON | SHGFI_SMALLICON
        file_attr = 0
        target_path = exe_path

        if not target_path or not os.path.exists(target_path):
            flags |= SHGFI_USEFILEATTRIBUTES
            file_attr = 0x80
            if not target_path.lower().endswith(".exe") and not target_path.lower().endswith(".ico"):
                target_path = ".exe"

        res = ctypes.windll.shell32.SHGetFileInfoW(
            target_path, file_attr, ctypes.byref(shfi), ctypes.sizeof(shfi), flags
        )

        if res != 0 and shfi.hIcon:
            return shfi.hIcon

        if os.path.exists(exe_path):
            h_small = ctypes.c_void_p()
            ret = ctypes.windll.shell32.ExtractIconExW(
                exe_path, 0, None, ctypes.byref(h_small), 1
            )
            if ret > 0 and h_small.value:
                return h_small.value

        return None

    @classmethod
    def _hicon_to_pil_via_draw(cls, hicon, width=16, height=16):
        if not HAS_PIL:
            return None

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        if not hdc_mem:
            user32.ReleaseDC(0, hdc_screen)
            return None

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = width
        bmi.biHeight = -height
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0

        p_bits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(
            hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(p_bits), None, 0
        )

        if not hbmp or not p_bits.value:
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(0, hdc_screen)
            return None

        h_old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

        DI_NORMAL = 0x0003
        success = user32.DrawIconEx(
            hdc_mem, 0, 0, hicon, width, height, 0, None, DI_NORMAL
        )

        if success:
            buffer_size = width * height * 4
            raw_bytes = ctypes.string_at(p_bits.value, buffer_size)
            img = Image.frombytes("RGBA", (width, height), raw_bytes, "raw", "BGRA")
        else:
            img = None

        gdi32.SelectObject(hdc_mem, h_old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        return img