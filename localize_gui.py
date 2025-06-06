import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
from localize_resources import ResourceLocalizer
from loguru import logger
import sys
import os

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ResourceLocalizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("资源本地化工具")
        
        # 初始化取消标志
        self.cancel_flag = False
        
        # 设置图标
        try:
            icon_path = get_resource_path("favicon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"加载图标失败: {str(e)}")
        
        # 配置根窗口的网格
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, sticky='nsew')
        
        # 配置主框架的网格
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # 创建输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入参数")
        input_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=2)
        
        # 配置输入框架的网格
        input_frame.grid_columnconfigure(1, weight=1)
        
        # 基础目录输入
        ttk.Label(input_frame, text="基础目录:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.base_dir_var = tk.StringVar()
        base_dir_entry = ttk.Entry(input_frame, textvariable=self.base_dir_var)
        base_dir_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Button(input_frame, text="浏览", command=self.browse_base_dir).grid(row=0, column=2, padx=5, pady=2)
        
        # 代理输入
        ttk.Label(input_frame, text="代理地址:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.proxy_var = tk.StringVar(value="127.0.0.1:7890")
        proxy_entry = ttk.Entry(input_frame, textvariable=self.proxy_var)
        proxy_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=2)
        button_frame.grid_columnconfigure(1, weight=1)  # 中间列占据所有空间，使按钮分散对齐
        
        # 开始按钮
        self.start_button = ttk.Button(button_frame, text="开始本地化", command=self.start_localization)
        self.start_button.grid(row=0, column=0, padx=5)
        
        # 取消按钮（初始禁用）
        self.cancel_button = ttk.Button(button_frame, text="取消本地化", command=self.cancel_localization, state='disabled')
        self.cancel_button.grid(row=0, column=2, padx=5)
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="日志输出")
        log_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=2)
        
        # 配置日志框架的网格
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky='nsew', padx=5, pady=2)
        
        # 配置日志文本框标签
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('SUCCESS', foreground='green')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        
        # 配置日志处理器
        self.setup_logger()
        
        # 设置最小窗口大小
        self.root.update_idletasks()
        min_width = max(input_frame.winfo_reqwidth(), log_frame.winfo_reqwidth()) + 20
        min_height = input_frame.winfo_reqheight() + button_frame.winfo_reqheight() + 200  # 给日志区域预留更多空间
        self.root.minsize(min_width, min_height)
        
        # 设置初始窗口大小
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = min(int(screen_width * 0.6), 800)
        height = min(int(screen_height * 0.7), 600)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_logger(self):
        """配置日志处理器"""
        logger.remove()  # 移除所有现有的处理器
        
        # 添加自定义处理器
        logger.add(self.log_handler, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
        
    def log_handler(self, message):
        """自定义日志处理器"""
        # 从消息中提取日志级别
        if "| ERROR |" in message:
            tag = 'ERROR'
        elif "| SUCCESS |" in message:
            tag = 'SUCCESS'
        elif "| WARNING |" in message:
            tag = 'WARNING'
        else:
            tag = 'INFO'
            
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def browse_base_dir(self):
        """浏览选择基础目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.base_dir_var.set(directory)
            
    def start_localization(self):
        """开始本地化过程"""
        base_dir = self.base_dir_var.get()
        proxy = self.proxy_var.get()
        
        if not base_dir:
            logger.error("请选择基础目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 重置取消标志
        self.cancel_flag = False
        
        # 禁用开始按钮，启用取消按钮
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # 在新线程中运行本地化过程
        thread = threading.Thread(target=self.run_localization, args=(base_dir, proxy))
        thread.daemon = True
        thread.start()
        
    def cancel_localization(self):
        """取消本地化过程"""
        self.cancel_flag = True
        logger.warning("正在取消本地化过程...")
        self.cancel_button.config(state=tk.DISABLED)
        
    def run_localization(self, base_dir, proxy):
        """运行本地化过程"""
        try:
            localizer = ResourceLocalizer(base_dir, proxy)
            
            def check_cancel():
                if self.cancel_flag:
                    raise Exception("用户取消了本地化过程")
                return True
            
            # 添加取消检查到localizer
            localizer.check_cancel = check_cancel
            
            localizer.process_directory()
            logger.success("资源本地化完成！")
        except Exception as e:
            if "用户取消了本地化过程" in str(e):
                logger.warning("本地化过程已取消")
            else:
                logger.error(f"处理过程中发生错误: {str(e)}")
        finally:
            # 重新启用开始按钮，禁用取消按钮
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))

def main():
    root = tk.Tk()
    # 设置窗口样式
    style = ttk.Style()
    style.configure('TLabelframe', padding=2)
    style.configure('TLabelframe.Label', padding=2)
    style.configure('TButton', padding=2)
    
    app = ResourceLocalizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 