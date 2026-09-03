import atexit
import ctypes
import os
import signal
import sys
import threading
from core.gpu_service import GPUService


class ProcessGuard:
    """进程生命周期与安全退出守护管理器"""

    _instance = None
    _lock = threading.Lock()
    _has_cleaned_up = False

    def __init__(self):
        self._custom_cleanup_callbacks = []

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def install(cls, additional_cleanup_cb=None):
        guard = cls.get_instance()
        if additional_cleanup_cb:
            guard.add_cleanup_callback(additional_cleanup_cb)

        atexit.register(guard.force_cleanup)
        guard._register_excepthook()
        guard._register_signals()

        if sys.platform == "win32":
            guard._register_win32_ctrl_handler()

        return guard

    def add_cleanup_callback(self, cb):
        if callable(cb) and cb not in self._custom_cleanup_callbacks:
            self._custom_cleanup_callbacks.append(cb)

    def force_cleanup(self):
        with self._lock:
            if ProcessGuard._has_cleaned_up:
                return
            ProcessGuard._has_cleaned_up = True

        for cb in self._custom_cleanup_callbacks:
            try:
                cb()
            except Exception:
                pass

        try:
            GPUService.reset_frequency()
        except Exception:
            pass

    def _register_excepthook(self):
        orig_excepthook = sys.excepthook

        def custom_excepthook(exc_type, exc_value, exc_traceback):
            try:
                self.force_cleanup()
            finally:
                if orig_excepthook:
                    orig_excepthook(exc_type, exc_value, exc_traceback)

        sys.excepthook = custom_excepthook

    def _register_signals(self):
        signals_to_catch = [signal.SIGINT, signal.SIGTERM]
        if hasattr(signal, "SIGBREAK"):
            signals_to_catch.append(signal.SIGBREAK)

        for sig in signals_to_catch:
            try:
                orig_handler = signal.getsignal(sig)

                def make_signal_handler(previous_handler):
                    def signal_handler(signum, frame):
                        self.force_cleanup()
                        if callable(previous_handler) and previous_handler not in (signal.SIG_IGN, signal.SIG_DFL):
                            previous_handler(signum, frame)
                        sys.exit(0)
                    return signal_handler

                signal.signal(sig, make_signal_handler(orig_handler))
            except Exception:
                pass

    def _register_win32_ctrl_handler(self):
        try:
            PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)

            def console_ctrl_handler(ctrl_type):
                if ctrl_type in (0, 1, 2, 5, 6):
                    self.force_cleanup()
                    return True
                return False

            self._win32_ctrl_routine = PHANDLER_ROUTINE(console_ctrl_handler)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(self._win32_ctrl_routine, True)
        except Exception:
            pass


install_process_guard = ProcessGuard.install
