@echo off
chcp 65001 >nul
echo === 计算机联锁模拟仿真系统 ===
echo.
echo 正在启动服务，请稍候...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo 启动失败！请确保已安装 Python 3.8+。
    echo 下载地址: https://www.python.org/downloads/
    pause
)
