# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包脚本：Nanako App Manager / GPUBooster_Main
# 说明：web / plugins / msi_service 等运行期数据目录由 post_build 脚本复制到 exe 旁，
#       以便 plugins 目录保持可扩展（可热插拔 .py 插件）。

block_cipher = None

a_main = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'psutil',
        'pynvml',
        'PIL',
        'winreg',
        'tkinter',
        'webview.platforms.edgechromium',   # pywebview Win 后端(EdgeChromium)
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_main = PYZ(a_main.pure, a_main.zipped_data, cipher=block_cipher)
exe_main = EXE(
    pyz_main,
    a_main.scripts,
    [],
    exclude_binaries=True,
    name='GPUBooster_Main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=True,               # 申请管理员权限
    icon='app_icon.ico',          # 嵌入主程序图标 (.ico)
)

coll = COLLECT(
    exe_main,
    a_main.binaries,
    a_main.zipfiles,
    a_main.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GPUBoosterAppSuite',
)
