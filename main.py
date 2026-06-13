import os
import threading
import webbrowser


os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")


def main() -> None:
    from interlocking_sim.web_gui import start_server

    url = start_server()

    tk_gui = None
    try:
        import tkinter as tk
        if tk.TkVersion >= 8.5:
            from interlocking_sim.gui import InterlockingApp
            tk_gui = InterlockingApp
    except Exception:
        pass

    print(f"浏览器访问地址: {url}")
    webbrowser.open(url)

    if tk_gui:
        print("检测到 Tkinter，已同时启动桌面窗口（浏览器界面仍可用）。")
        app = tk_gui()
        app.mainloop()
    else:
        print("提示: 按 Ctrl+C 停止服务。")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
