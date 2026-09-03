# Nanako App Manager（NVIDIA 显卡高频锁频工具 / GPUBooster）

一款面向 Windows 的 **GPU 频率管理 + 软件调度中心**：后台监控当前运行/前台聚焦的程序，自动将 NVIDIA 显卡核心频率**锁定或限制**到预设区间，并联动微星小飞机（MSI Afterburner）应用超频预设；同时提供软件库管理、分类分组、排队调度、使用统计、电源计划自动切换与可扩展插件体系，内置毛玻璃拟态风格的 WebView2 图形界面。

- **中文说明**：本文件（README.md）
- **English**: [README.en.md](README.en.md)
- 下载安装包/便携版：见本仓库 Releases 页

## 功能特性

### GPU 频率管理
- **进程级自动化锁频**：支持“前台焦点窗口精准识别”与“系统全部进程识别”两种监控模式（全局模式开关）。
- **定频 / 频段两种策略**：可将 GPU 核心频率锁定在固定值，或限制在安全的最高/最低区间内。
- **平滑调频缓冲**：频率调整按阶梯平滑过渡（步长/延时可调），避免瞬时跳频。
- **硬件安全保护**：基于 NVIDIA 官方 `nvidia-ml-py`(NVML) 内存级接口探测显卡状态，失败自动回退 `nvidia-smi` 双通道扫描；下发锁频指令前自动查询硬件允许的最高 Boost 频率并截断超限数值。
- **微星小飞机深度联动**：每条规则可绑定 Afterburner 配置方案，一键唤起并打开 V-F 频率电压曲线编辑器（降压超频入口）。
- **电源计划联动**：按应用自动切换 Windows 电源计划，退出后恢复默认。
- **全局热键**：默认 `F12` 一键启停监控（可配置）。

### 软件管理
- 软件库：手动添加 / 一键抓取前台窗口 / 扫描已安装程序（含控制面板应用）/ 批量导入外部可执行文件。
- 分类与分组：自定义分类、按组统一下发策略（跟随组配置），支持批量改类、批量删除。
- 排队器模式与焦点模式双调度；统计每个应用的使用时长（今日/本周/累计）、启动次数、最近运行时间，自动标记“未使用”便于清理。
- 全局搜索、在线搜索（Bing / B 站等，可自定义搜索 URL，支持代理）。

### 界面与数据
- 毛玻璃拟态 UI：自定义壁纸（图片或 Base64）、透明度、模糊度、主题强调色/文本色、侧栏折叠。
- 设置/软件库数据导出与导入（JSON 备份）。
- 插件体系：`plugins` 目录下的 `.py` 插件启动时自动发现加载（监控、设置、统计、代理、网页搜索、MSI 等），安装目录内可直接扩展。
- 应用自保护进程守卫、管理员权限自动提权（UAC）、可选开机自启。

## 运行环境

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10 / 11 64 位 |
| 显卡（GPU 功能） | NVIDIA GeForce / RTX 系列，驱动需支持 `nvidia-smi` |
| 运行时 | Microsoft Edge WebView2 Runtime（Win10/11 通常已内置） |
| 管理员权限 | GPU 锁频指令受 NVIDIA 驱动限制，必须以管理员运行（程序会自动弹出 UAC 提权） |
| 源码运行（可选） | Python 3.10+，`pip install nvidia-ml-py psutil pillow pywebview pythonnet` |

> 说明：软件管理/统计等基础功能不依赖 NVIDIA 显卡；锁频类功能仅对 NVIDIA 有效，A 卡暂无适配。

## 安装与使用

1. 在 Releases 下载 `GPUBooster_Setup_v*.exe`（安装版）或便携版压缩包。
2. 安装版按向导安装（需管理员确认）；便携版解压后运行 `GPUBooster_Main.exe`。
3. 首次使用流程：
   - 在“软件库”中扫描已安装程序或添加目标程序；
   - 为目标程序设置 GPU 模式（定频/频段）、频率上下限、电源计划、MSI 配置方案；
   - 点击“开启监控”或按全局热键 `F12`：目标程序运行/获得焦点时自动套用频率策略，退出后自动恢复默认。

## 从源码构建

```powershell
# 1. 创建虚拟环境并安装依赖
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install pyinstaller pywebview pythonnet clr_loader psutil pillow nvidia-ml-py pywin32-ctypes

# 2. 直接运行（开发）
.\.venv\Scripts\python main.py

# 3. 普通打包：PyInstaller 生成便携目录 dist\GPUBoosterAppSuite
.\.venv\Scripts\pyinstaller --noconfirm --clean app_build.spec
#    构建后需将 web / plugins / msi_service / readme.txt 复制到 exe 旁（插件热插拔依赖）

# 4. Inno Setup 打包：生成 installer_output\GPUBooster_Setup_v1.1.exe
& 'G:\Inno Setup 6\ISCC.exe' setup_script.iss
```

## 目录结构

```
main.py                 入口（pywebview 窗口 + 提权 + 热键 + 监控装配）
api_bridge.py           前后端统一网关 API（pywebview js_api）
app_build.spec          PyInstaller 打包配置
setup_script.iss        Inno Setup 安装包脚本
app_icon.ico            程序 / 安装包图标
core/                   GPU 服务、电源计划、监控调度、数据管理、进程守卫等
plugins/                插件体系（自动发现加载，可扩展）
msi_service/            MSI Afterburner 交互（注册表/路径扫描、曲线编辑器唤起）
web/                    WebView2 前端（css/js/views，毛玻璃拟态 UI）
software_library.json   本地软件库与设置数据（运行时生成/维护）
```

## 常见问题

- **提示未获得管理员权限？** NVIDIA 驱动对频率修改指令有硬性限制，必须以管理员身份运行；普通权限启动会自动弹出 UAC。
- **提示 pynvml Warning？** 请卸载旧的三方 `pynvml` 包并安装官方维护的 `nvidia-ml-py`：`pip uninstall pynvml -y` 后 `pip install nvidia-ml-py`。
- **微星小飞机未安装/未运行？** 程序会自动扫描注册表与常见安装路径；规则若未绑定配置方案则不会向 Afterburner 发送命令。
- **没有 NVIDIA 显卡或 nvidia-smi 不可用？** GPU 锁频功能不可用，其余软件管理功能不受影响。

## 风险提示

超频、降压、锁频属于硬件改动行为，可能导致系统不稳定、蓝屏甚至硬件损坏。本工具内置硬件极限探测与超限截断保护，**但请务必在理解风险的前提下使用，后果自负**。建议先用小幅度频率验证稳定性，再逐步调整。

## License

本项目代码仅供学习交流，请勿用于商业用途。
