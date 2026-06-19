import os


os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")


def _run_web_fallback(reason: str) -> None:
    import threading
    import webbrowser

    from interlocking_sim.web_gui import start_server

    url = start_server()
    print(f"{reason}，已自动切换到浏览器承载界面。")
    print(f"浏览器访问地址: {url}")
    webbrowser.open(url)
    print("提示: 按 Ctrl+C 停止服务。")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


def main() -> None:
    try:
        import tkinter as tk
    except Exception as exc:
        _run_web_fallback(f"检测到 Tkinter 不可用({exc.__class__.__name__})")
        return

    if tk.TkVersion < 8.5:
        _run_web_fallback(f"检测到 Tk 版本过低({tk.TkVersion})")
        return

    try:
        from interlocking_sim.gui import InterlockingApp
    except ModuleNotFoundError as exc:
        if exc.name != "_tkinter":
            raise
        _run_web_fallback("检测到缺少 _tkinter 扩展")
        return

    print("检测到 Tkinter，启动桌面窗口。")
    app = InterlockingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
