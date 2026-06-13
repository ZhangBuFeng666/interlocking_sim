#!/usr/bin/env bash
set -e
echo "=== 计算机联锁模拟仿真系统 macOS 构建工具 ==="
echo ""

cd "$(dirname "$0")"

# Ensure py2app is available
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "[1/3] 安装 py2app..."
    python3 -m venv venv 2>/dev/null || true
    source venv/bin/activate 2>/dev/null || true
    pip install py2app
fi

echo "[1/3] 清理旧构建..."
rm -rf build dist "计算机联锁模拟仿真系统.app"

echo "[2/3] 构建 .app..."
python3 setup.py py2app --dist-dir .

echo "[3/3] 构建完成！"
echo ""
echo "输出: 计算机联锁模拟仿真系统.app"
echo "双击即可运行。"
