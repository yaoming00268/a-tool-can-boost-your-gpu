import sys
import os
import shutil
import ctypes
import base64
import io

if sys.platform == "win32":
    import winreg
else:
    winreg = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from PIL import Image
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
    """应用程序图标提取与任意图片转换 Base64 服务"""

    _b64_cache = {}

    @classmethod
    def resolve_path(cls, path):
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

            if winreg:
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

            if HAS_PSUTIL:
                try:
                    for p in psutil.process_iter(['name', 'exe']):
                        if p.info['name'] and p.info['name'].lower() == exe_name.lower():
                            if p.info['exe'] and os.path.exists(p.info['exe']):
                                return p.info['exe']
                except Exception:
                    pass
        return path

    @classmethod
    def convert_image_file_to_base64(cls, file_path):
        default_svg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48'><rect width='48' height='48' fill='%232563EB' rx='8'/></svg>"
        if not file_path or not os.path.exists(file_path):
            return default_svg

        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.ico', '.webp'] and HAS_PIL:
            try:
                img = Image.open(file_path)
                img = img.convert("RGBA")
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                return f"data:image/png;base64,{b64}"
            except Exception:
                pass
        return cls.get_icon_base64(file_path)

    @classmethod
    def get_icon_base64(cls, exe_path=""):
        key = (exe_path or "").lower()
        if key in cls._b64_cache:
            return cls._b64_cache[key]

        res = cls._extract_base64(exe_path)
        cls._b64_cache[key] = res
        return res

    @classmethod
    def _extract_base64(cls, exe_path):
        default_svg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48'><rect width='48' height='48' fill='%23555' rx='8'/></svg>"
        if sys.platform != "win32" or not HAS_PIL:
            return default_svg

        resolved = cls.resolve_path(exe_path)
        hicon = cls._get_hicon(resolved if resolved else exe_path)
        if not hicon:
            return default_svg

        pil_img = cls._hicon_to_pil_via_draw(hicon, width=48, height=48)
        ctypes.windll.user32.DestroyIcon(hicon)

        if pil_img:
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            b64_str = base64.b64encode(buf.getvalue()).decode()
            return f"data:image/png;base64,{b64_str}"
        return default_svg

    @classmethod
    def _get_hicon(cls, exe_path):
        shfi = SHFILEINFO()
        flags = 0x000000100 | 0x000000000
        target_path = exe_path

        if not target_path or not os.path.exists(target_path):
            flags |= 0x000000010
            file_attr = 0x80
            if not target_path.lower().endswith(".exe") and not target_path.lower().endswith(".ico"):
                target_path = ".exe"
        else:
            file_attr = 0

        res = ctypes.windll.shell32.SHGetFileInfoW(
            target_path, file_attr, ctypes.byref(shfi), ctypes.sizeof(shfi), flags
        )
        if res != 0 and shfi.hIcon:
            return shfi.hIcon

        if os.path.exists(exe_path):
            h_large = ctypes.c_void_p()
            ret = ctypes.windll.shell32.ExtractIconExW(exe_path, 0, ctypes.byref(h_large), None, 1)
            if ret > 0 and h_large.value:
                return h_large.value
        return None

    @classmethod
    def _hicon_to_pil_via_draw(cls, hicon, width=48, height=48):
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
        hbmp = gdi32.CreateDIBSection(hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(p_bits), None, 0)
        if not hbmp or not p_bits.value:
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(0, hdc_screen)
            return None

        h_old_bmp = gdi32.SelectObject(hdc_mem, hbmp)
        success = user32.DrawIconEx(hdc_mem, 0, 0, hicon, width, height, 0, None, 0x0003)

        if success:
            raw_bytes = ctypes.string_at(p_bits.value, width * height * 4)
            img = Image.frombytes("RGBA", (width, height), raw_bytes, "raw", "BGRA")
        else:
            img = None

        gdi32.SelectObject(hdc_mem, h_old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)
        return img
