import ctypes
import platform

SPI_GETWORKAREA = 0x0030


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def get_work_area():
    """
    Returns (width, height) of the usable screen area (excludes the
    taskbar). Returns None on non-Windows systems or if the call fails.
    """
    if platform.system() != "Windows":
        return None

    try:
        rect = _RECT()
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
        )
        return (rect.right - rect.left), (rect.bottom - rect.top)
    except Exception:
        return None


def size_and_center(win, width_ratio=0.9, height_ratio=0.88, resizable=False):
    """
    Sizes `win` as a ratio of the real usable screen area and centers
    it - adapts automatically to any monitor size/resolution/scaling.
    """
    work_area = get_work_area()

    if work_area:
        area_width, area_height = work_area
    else:
        area_width = win.winfo_screenwidth()
        area_height = win.winfo_screenheight()

    width = int(area_width * width_ratio)
    height = int(area_height * height_ratio)

    x = (area_width - width) // 2
    y = (area_height - height) // 2

    win.geometry(f"{width}x{height}+{x}+{y}")
    win.resizable(resizable, resizable)