import PyInstaller.__main__
import os

# 确保图标文件存在
if not os.path.exists('favicon.ico'):
    raise FileNotFoundError("找不到 favicon.ico 文件，请确保它在当前目录中")

PyInstaller.__main__.run([
    'localize_gui.py',
    '--name=资源本地化工具',
    '--onefile',
    '--windowed',
    '--icon=favicon.ico',
    '--add-data=favicon.ico;.',
    '--add-data=localize_resources.py;.',
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=loguru',
    '--hidden-import=beautifulsoup4',
    '--hidden-import=chardet',
    '--hidden-import=brotli',
    '--clean',
    '--noconfirm',
    # 添加日志等级环境变量
    '--add-binary=favicon.ico;.'
]) 