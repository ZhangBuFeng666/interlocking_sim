from setuptools import setup

APP = ["main.py"]
APP_NAME = "计算机联锁模拟仿真系统"

DATA_FILES = []

OPTIONS = {
    "argv_emulation": False,
    "iconfile": None,
    "plist": {
        "CFBundleName": "计算机联锁模拟仿真系统",
        "CFBundleDisplayName": "计算机联锁模拟仿真系统",
        "CFBundleIdentifier": "local.interlocking.sim",
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "CFBundleDevelopmentRegion": "zh_CN",
        "NSHighResolutionCapable": True,
    },
    "packages": ["interlocking_sim"],
    "includes": ["tkinter"],
    "excludes": ["pytest", "test"],
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
