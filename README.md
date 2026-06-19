# 计算机联锁模拟仿真系统

跨平台联锁模拟系统，支持 **Windows / macOS / Linux**。仅使用 Python 标准库，无外部依赖。

---

## 快速启动

### 方式一：运行源码（所有平台）

需要安装 Python 3.8+（[python.org](https://www.python.org/downloads/)），Tkinter 已内置在 Python 中。

```bash
python main.py
# 或双击 run.bat (Windows) / run.sh (macOS/Linux)
```

程序会优先启动 Tkinter 桌面窗口；如果当前环境缺少 Tkinter 或 Tk 版本过低，则自动切换为本机浏览器承载界面，并打开 `http://127.0.0.1:8765`。

### 方式二：macOS 独立 .app

双击 `计算机联锁模拟仿真系统.app` 即可运行（已内置 Python 和 Tkinter）。

### 方式三：Windows 独立 .exe

在 Windows 上运行 `build_win.bat`，自动打包为 `dist/InterlockingSim.exe`：

```cmd
build_win.bat
```

---

## 构建独立包

### macOS

```bash
./build_mac.sh        # 一键构建 .app
```

### Windows

在 Windows 上运行：
```cmd
build_win.bat         # 自动安装 PyInstaller 并打包 .exe
```

---

## 运行测试

```bash
python -m unittest discover -s tests
```

---

## 项目结构

| 文件 | 说明 |
|------|------|
| `main.py` | 入口：优先启动 Tkinter 桌面窗口，Tk 不可用时回退到 Web 界面 |
| `interlocking_sim/web_gui.py` | 浏览器 Web 界面（Canvas 站场图） |
| `interlocking_sim/gui.py` | Tkinter 桌面界面 |
| `interlocking_sim/model.py` | 数据模型（轨道、信号、道岔、进路） |
| `interlocking_sim/interlocking.py` | 联锁逻辑控制器 |
| `docs/` | 设计文档、测试报告、演示流程 |

详细设计见 `docs/design.md`，测试报告见 `docs/test_report.md`。
