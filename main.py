import os


os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

try:
    from interlocking_sim.gui import main
except ModuleNotFoundError as exc:
    if exc.name != "_tkinter":
        raise
    from interlocking_sim.web_gui import main


if __name__ == "__main__":
    main()
