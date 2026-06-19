@echo off
chcp 65001 >nul
title 计算机联锁模拟仿真系统 - Windows 构建

echo === 计算机联锁模拟仿真系统 Windows 构建工具 ===
echo.
echo 本脚本将在 Windows 上打包为独立 .exe
echo 需要安装 Python 3.8+ (https://www.python.org/downloads/)
echo.

REM 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装。
    pause
    exit /b 1
)

echo [1/4] 安装 PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败。
    pause
    exit /b 1
)

echo [2/4] 清理旧构建...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [3/4] 构建 .exe...
pyinstaller --onefile --console ^
    --name "InterlockingSim" ^
    --add-data "interlocking_sim;interlocking_sim" ^
    --hidden-import tkinter ^
    --hidden-import interlocking_sim ^
    --hidden-import interlocking_sim.model ^
    --hidden-import interlocking_sim.interlocking ^
    --hidden-import interlocking_sim.web_gui ^
    --hidden-import interlocking_sim.gui ^
    main.py
if errorlevel 1 (
    echo [错误] 构建失败。
    pause
    exit /b 1
)

echo [4/4] 构建完成！
echo.
echo 输出文件: dist\InterlockingSim.exe
echo 双击运行将优先启动桌面窗口；若 Tkinter 不可用，则自动启动浏览器界面。
echo.
pause
