# 计算机联锁模拟仿真系统

运行环境：Python 3.10+，仅使用标准库 Tkinter 和 unittest。

运行桌面软件，推荐直接双击以下任一入口：

```text
启动联锁模拟软件.command
InterlockingSim.app
```

也可以用命令运行，注意 `main.py` 后面不要加中文句号：

```bash
/usr/bin/python3 main.py
```

macOS 自带 Python 通常包含 Tkinter，可直接运行桌面版软件：

```bash
/usr/bin/python3 main.py
```

如果当前 Python 缺少 `_tkinter`，程序会自动切换到单机浏览器承载界面，并在浏览器打开 `http://127.0.0.1:8765`。该模式仍是本机软件的一部分，不依赖互联网或外部服务；功能与桌面版一致。

运行测试：

```bash
python3 -m unittest discover -s tests
```

项目包含上位机界面、后台联锁逻辑、现场设备仿真和测试文档。详细设计见 `docs/design.md`，测试报告见 `docs/test_report.md`。
