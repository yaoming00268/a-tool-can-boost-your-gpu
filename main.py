import sys
import tkinter as tk
from gpu_service import elevate_privileges, is_admin
from ui_app.app_main import GPUFrequencyBoosterApp


def main():
    if sys.platform == "win32" and not is_admin():
        elevate_privileges()
    root = tk.Tk()
    app = GPUFrequencyBoosterApp(root)
    root.mainloop()
if __name__ == "__main__":
    main()