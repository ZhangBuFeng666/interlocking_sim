import os


os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

_FALLBACK_REASON = ""


def _select_entrypoint():
    global _FALLBACK_REASON
    try:
        import tkinter as tk
    except Exception as exc:
        _FALLBACK_REASON = f"Tk 不可用({exc.__class__.__name__})"
        from interlocking_sim.web_gui import main as web_main
        return web_main

    if tk.TkVersion < 8.6:
        _FALLBACK_REASON = f"Tk 版本过低({tk.TkVersion})"
        from interlocking_sim.web_gui import main as web_main
        return web_main

    try:
        from interlocking_sim.gui import main as gui_main
        return gui_main
    except ModuleNotFoundError as exc:
        if exc.name != "_tkinter":
            raise
        _FALLBACK_REASON = "缺少 _tkinter 扩展"
        from interlocking_sim.web_gui import main as web_main
        return web_main


main = _select_entrypoint()


if __name__ == "__main__":
    if _FALLBACK_REASON:
        print(f"检测到 {_FALLBACK_REASON}，自动切换到浏览器承载界面。")
    main()
