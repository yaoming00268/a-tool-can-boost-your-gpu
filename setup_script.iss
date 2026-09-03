; =========================================================
; Inno Setup 自动化安装包构建脚本
; =========================================================

#define MyAppName "NVIDIA 显卡高频锁频工具"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "GPUBooster Studio"
#define MyAppExeName "GPUBooster_Main.exe"
#define MyAppIcon "app_icon.ico"

[Setup]
; 软件基本信息
AppId={{8F54A21C-3B49-4D8E-B231-1C904E1FDE43}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; 默认安装路径与路径选择配置
DefaultDirName={autopf}\GPUBooster
DefaultGroupName={#MyAppName}

; 输出与图标配置
OutputDir=installer_output
OutputBaseFilename=GPUBooster_Setup_v1.1
SetupIconFile={#MyAppIcon}
Compression=lzma2/max
SolidCompression=yes

; 提示提升管理员权限安装
PrivilegesRequired=admin
; 控制面板中显示的卸载图标
UninstallDisplayIcon={app}\{#MyAppExeName}
; 控制面板中的正式名称
UninstallDisplayName={#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 打包所有文件 (如果之前修改了 dist 下的输出目录名，请确保这里的路径和 dist 下一致)
Source: "dist\GPUBoosterAppSuite\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 创建开始菜单和桌面快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; 安装完成后提示运行主程序
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
