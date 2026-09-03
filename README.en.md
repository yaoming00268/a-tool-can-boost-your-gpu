# Nanako App Manager (NVIDIA GPU Clock-Lock Tool / GPUBooster)

A **GPU frequency management + software scheduling center** for Windows: it watches foreground/running processes in the background and automatically **locks or clamps your NVIDIA GPU core clock** to per-app presets, integrates with MSI Afterburner overclocking profiles — while also offering a software library manager with categories, groups, queue scheduling, usage statistics, per-app power-plan switching and an extensible plugin system, all wrapped in a glassmorphism WebView2 UI.

- **中文说明**：[README.md](README.md)
- Downloads (installer / portable): see the **Releases** page of this repository

## Features

### GPU Clock Management
- **Process-level automation**: monitor the *focused foreground window* or *all running processes* (global-mode switch).
- **Two strategies per app**: lock the GPU core clock to a fixed frequency, or clamp it within a safe min/max band.
- **Smooth ramping buffer**: frequency changes step up/down gradually (adjustable step & delay) to avoid abrupt jumps.
- **Hardware safety**: probes the GPU through NVIDIA's official `nvidia-ml-py` (NVML) in-process API with automatic fallback to `nvidia-smi`; before applying a lock, the hardware's real max boost frequency is queried and over-limit values are automatically truncated.
- **MSI Afterburner integration**: bind any rule to an Afterburner profile, wake it up and open the V-F curve editor (undervolt+overclock entry point) on demand.
- **Power plan per app**: switches Windows power plans automatically when an app runs and restores the default afterwards.
- **Global hotkey**: default `F12` toggles monitoring on/off (configurable).

### Software Management
- Library: add manually, capture the foreground window in one click, scan installed programs (incl. Control Panel apps), or import external executables in batch.
- Categories & groups: custom categories, group-level policy sync (`follow group`), batch re-categorize / delete.
- Dual scheduling modes: **focus mode** and **queue mode**; per-app usage stats (today / this week / total duration, launch count, last run) with automatic "unused" detection.
- Global search and online search (Bing / Bilibili / customizable URL, proxy supported).

### UI & Data
- Glassmorphism UI: custom wallpaper (image file or Base64), opacity, blur, accent/text colors, collapsible sidebar.
- Settings & library export/import as JSON backup.
- Plugin system: any `.py` file dropped into the `plugins` folder is auto-discovered and loaded at startup (monitor, settings, stats, proxy, web-search, MSI…), so the installed app stays extensible.
- Process self-guard, automatic UAC elevation, optional start-with-Windows.

## Requirements

| Item | Requirement |
| --- | --- |
| OS | Windows 10 / 11 (64-bit) |
| GPU (clock features) | NVIDIA GeForce / RTX with an `nvidia-smi`-capable driver |
| Runtime | Microsoft Edge WebView2 Runtime (usually preinstalled on Win10/11) |
| Privileges | Clock-lock commands are restricted by NVIDIA drivers — run as Administrator (the app requests UAC automatically) |
| Run from source (optional) | Python 3.10+, `pip install nvidia-ml-py psutil pillow pywebview pythonnet` |

> Note: library/statistics features work without an NVIDIA GPU; clock-locking is NVIDIA-only (AMD is untested).

## Install & Use

1. Grab `GPUBooster_Setup_v*.exe` (installer) or the portable archive from **Releases**.
2. Run the installer (admin prompt), or extract the portable build and launch `GPUBooster_Main.exe`.
3. First-run flow:
   - In *Library*, scan installed apps or add your target programs;
   - Configure each app's GPU mode (lock / clamp), min-max frequencies, power plan, MSI profile;
   - Press **Start Monitor** (or hotkey `F12`): the preset is applied while the app runs / has focus and restored automatically when it exits.

## Build from Source

```powershell
# 1. Create a virtual env and install dependencies
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install pyinstaller pywebview pythonnet clr_loader psutil pillow nvidia-ml-py pywin32-ctypes

# 2. Run in dev mode
.\.venv\Scripts\python main.py

# 3. Portable build (PyInstaller) -> dist\GPUBoosterAppSuite
.\.venv\Scripts\pyinstaller --noconfirm --clean app_build.spec
#    After building, copy web / plugins / msi_service / readme.txt next to the exe
#    (plugins stay hot-loadable this way).

# 4. Installer (Inno Setup) -> installer_output\GPUBooster_Setup_v1.1.exe
& 'G:\Inno Setup 6\ISCC.exe' setup_script.iss
```

## Project Layout

```
main.py                 Entry point (pywebview window, elevation, hotkey, monitor wiring)
api_bridge.py           Unified gateway API for the frontend (pywebview js_api)
app_build.spec          PyInstaller build config
setup_script.iss        Inno Setup script
app_icon.ico            App / installer icon
core/                   GPU service, power plans, monitor core, data manager, process guard…
plugins/                Plugin framework (auto-discovered, extensible)
msi_service/            MSI Afterburner interaction (registry/path scan, V-F editor launch)
web/                    WebView2 frontend (css/js/views, glassmorphism UI)
software_library.json   Local library & settings data (generated at runtime)
```

## FAQ

- **"Not running as administrator"?** NVIDIA drivers hard-restrict clock-change commands — run as admin; the app raises UAC by itself when launched with normal privileges.
- **`pynvml` Warning printed?** Uninstall the old third-party `pynvml` package and use the official one: `pip uninstall pynvml -y`, then `pip install nvidia-ml-py`.
- **MSI Afterburner not installed / not running?** The app scans the registry and common install paths. Rules that are not bound to a profile send no commands to Afterburner at all.
- **No NVIDIA GPU or no `nvidia-smi`?** Clock-lock features are unavailable; everything else keeps working.

## Disclaimer

Overclocking / undervolting / clock-locking can make your system unstable, blue-screen, or even damage hardware. This tool includes hardware-limit probing and over-limit truncation, but **use it at your own risk**. Always validate stability with a small frequency change first.

## License

For learning and personal use only. Not for commercial purposes.
