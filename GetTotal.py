import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import re
from pathlib import Path
from datetime import datetime
import webbrowser
import threading
import queue
import hashlib

class CodeAnalyzer:
    """代码分析器"""
    
    # 默认语言配置
    DEFAULT_LANGUAGES = {
        "C/C++": {
            "extensions": [".c", ".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "C#": {
            "extensions": [".cs"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "Python": {
            "extensions": [".py", ".pyw"],
            "single_line_comment": "#",
            "multi_line_comment": [('"""', '"""'), ("'''", "'''")],
            "string_delimiters": ['"', "'"]
        },
        "Java": {
            "extensions": [".java"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "Kotlin": {
            "extensions": [".kt", ".kts"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "JavaScript/TypeScript": {
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'", '`']
        },
        "HTML/CSS": {
            "extensions": [".html", ".htm", ".css", ".scss", ".sass", ".less"],
            "single_line_comment": "//",
            "multi_line_comment": [("<!--", "-->"), ("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "PHP": {
            "extensions": [".php", ".php3", ".php4", ".php5", ".phtml"],
            "single_line_comment": ["//", "#"],
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "Ruby": {
            "extensions": [".rb", ".rbw", ".rake"],
            "single_line_comment": "#",
            "multi_line_comment": [("=begin", "=end")],
            "string_delimiters": ['"', "'"]
        },
        "Rust": {
            "extensions": [".rs"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "Go": {
            "extensions": [".go"],
            "single_line_comment": "//",
            "multi_line_comment": [("/*", "*/")],
            "string_delimiters": ['"', "'"]
        },
        "Shell": {
            "extensions": [".sh", ".bash", ".zsh", ".fish"],
            "single_line_comment": "#",
            "multi_line_comment": [],
            "string_delimiters": ['"', "'"]
        },
        "Assembly": {
            "extensions": [".asm", ".s", ".S"],
            "single_line_comment": [";", "#"],
            "multi_line_comment": [],
            "string_delimiters": ['"', "'"]
        }
    }
    
    @staticmethod
    def analyze_file(file_path, language_config):
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            return None
        
        total_lines = len(lines)
        empty_lines = 0
        comment_lines = 0
        code_lines = 0
        
        in_block_comment = False
        block_comment_start = None
        block_comment_end = None
        
        # 处理多行注释标记
        multi_line_comments = language_config.get("multi_line_comment", [])
        
        for line in lines:
            stripped_line = line.strip()
            
            # 检查空行
            if not stripped_line:
                empty_lines += 1
                continue
            
            # 检查多行注释
            line_comment_check = stripped_line
            
            # 处理多行注释
            if multi_line_comments:
                for start_marker, end_marker in multi_line_comments:
                    if not in_block_comment:
                        if start_marker in line_comment_check:
                            # 检查注释是否在同一行开始和结束
                            if end_marker in line_comment_check:
                                # 找到结束标记在开始标记之后的位置
                                start_idx = line_comment_check.find(start_marker)
                                end_idx = line_comment_check.find(end_marker, start_idx + len(start_marker))
                                if end_idx != -1:
                                    # 整个注释在同一行
                                    comment_lines += 1
                                    # 检查注释后是否有代码
                                    after_comment = line_comment_check[end_idx + len(end_marker):].strip()
                                    if after_comment:
                                        # 如果有代码，这行既是注释也是代码
                                        code_lines += 1
                                    line_comment_check = ""
                                    break
                            else:
                                # 多行注释开始
                                in_block_comment = True
                                block_comment_start = start_marker
                                block_comment_end = end_marker
                                comment_lines += 1
                                line_comment_check = ""
                                break
                    else:
                        # 在多行注释中
                        comment_lines += 1
                        if block_comment_end in line_comment_check:
                            # 多行注释结束
                            in_block_comment = False
                            block_comment_start = None
                            block_comment_end = None
                        line_comment_check = ""
                        break
            
            # 如果已经确定为注释行，跳过后续检查
            if not line_comment_check:
                continue
            
            # 检查单行注释
            is_comment = False
            single_line_comments = language_config.get("single_line_comment", [])
            if not isinstance(single_line_comments, list):
                single_line_comments = [single_line_comments]
            
            for comment_marker in single_line_comments:
                if comment_marker and line_comment_check.startswith(comment_marker):
                    comment_lines += 1
                    is_comment = True
                    break
            
            if not is_comment:
                code_lines += 1
        
        return {
            "total_lines": total_lines,
            "empty_lines": empty_lines,
            "comment_lines": comment_lines,
            "code_lines": code_lines,
            "file_path": str(file_path),
            "file_name": os.path.basename(file_path)
        }
    
    @staticmethod
    def get_language_from_extension(file_path, language_configs):
        """根据文件扩展名获取语言"""
        ext = Path(file_path).suffix.lower()
        for lang, config in language_configs.items():
            if "extensions" in config and ext in config["extensions"]:
                return lang
        return "Unknown"

class ModernCodeCounterApp:
    """现代代码统计工具应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("代码统计工具 - Modern Code Counter")
        self.root.geometry("1200x800")
        
        # 设置应用程序图标
        try:
            self.root.iconbitmap(default=self.get_icon_path())
        except:
            pass
        
        # 初始化配置
        self.config = self.load_config()
        self.results = {}
        self.comparison_results = {}
        self.current_directory = ""
        self.is_dark_mode = self.config.get("dark_mode", True)
        self.language_configs = self.config.get("language_configs", CodeAnalyzer.DEFAULT_LANGUAGES)
        self.include_patterns = self.config.get("include_patterns", ["*"])
        self.exclude_patterns = self.config.get("exclude_patterns", [])
        
        # 设置样式
        self.setup_styles()
        
        # 创建UI
        self.setup_ui()
        
        # 绑定事件
        self.bind_events()
        
        # 加载自定义语言配置
        self.load_custom_language_configs()
        
        # 应用初始主题
        self.apply_theme()
    
    def get_icon_path(self):
        """获取图标路径（尝试多种方式）"""
        icon_paths = [
            "icon.ico",
            "resources/icon.ico",
            os.path.join(os.path.dirname(__file__), "icon.ico")
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                return path
        
        # 如果没有找到图标文件，返回None
        return None
    
    def setup_styles(self):
        """设置现代扁平化样式"""
        self.style = ttk.Style()
        
        # 设置主题
        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")
        elif "alt" in available_themes:
            self.style.theme_use("alt")
        
        # 深色模式颜色
        self.dark_bg = "#1e1e1e"
        self.dark_fg = "#f0f0f0"
        self.dark_select = "#3a3a3a"
        self.dark_accent = "#007acc"
        self.dark_success = "#4caf50"
        self.dark_warning = "#ff9800"
        self.dark_error = "#f44336"
        self.dark_hover = "#505050"
        self.dark_active = "#606060"
        
        # 浅色模式颜色
        self.light_bg = "#f5f5f5"
        self.light_fg = "#333333"
        self.light_select = "#e0e0e0"
        self.light_accent = "#007acc"
        self.light_success = "#4caf50"
        self.light_warning = "#ff9800"
        self.light_error = "#f44336"
        self.light_hover = "#d0d0d0"
        self.light_active = "#c0c0c0"
        
    def setup_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建顶部工具栏
        self.create_toolbar(main_frame)
        
        # 创建内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 左侧控制面板
        left_panel = ttk.Frame(content_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # 右侧结果显示区域
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧控制面板内容
        self.create_left_panel(left_panel)
        
        # 右侧结果显示区域内容
        self.create_right_panel(right_panel)
        
        # 状态栏
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮组
        button_frame = ttk.Frame(toolbar)
        button_frame.pack(side=tk.LEFT)
        
        # 工具栏按钮
        buttons = [
            ("选择目录", self.select_directory, "📁"),
            ("开始统计", self.start_analysis, "▶️"),
            ("停止", self.stop_analysis, "⏹️"),
            ("导出结果", self.export_results, "📤"),
            ("导入结果", self.import_results, "📥"),
            ("比较结果", self.compare_results, "🔄"),
            ("设置", self.open_settings, "⚙️"),
            ("关于", self.open_about, "ℹ️"),
        ]
        
        for text, command, emoji in buttons:
            btn = ttk.Button(
                button_frame, 
                text=f" {emoji} {text}", 
                command=command,
                style="Accent.TButton" if text == "开始统计" else "TButton"
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # 主题切换按钮
        self.theme_btn = ttk.Button(
            button_frame, 
            text=" 🌙 深色模式" if not self.is_dark_mode else " ☀️ 浅色模式", 
            command=self.toggle_theme
        )
        self.theme_btn.pack(side=tk.LEFT, padx=10)
        
        # 当前目录显示
        self.dir_label = ttk.Label(toolbar, text="未选择目录")
        self.dir_label.pack(side=tk.RIGHT, padx=10)
    
    def create_left_panel(self, parent):
        """创建左侧控制面板"""
        # 面板标题
        ttk.Label(parent, text="统计配置", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))
        
        # 文件过滤配置
        filter_frame = ttk.LabelFrame(parent, text="文件过滤", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 包含模式
        ttk.Label(filter_frame, text="包含模式 (多个用逗号分隔):").pack(anchor=tk.W)
        self.include_entry = ttk.Entry(filter_frame)
        self.include_entry.insert(0, ", ".join(self.include_patterns))
        self.include_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 排除模式
        ttk.Label(filter_frame, text="排除模式 (多个用逗号分隔):").pack(anchor=tk.W)
        self.exclude_entry = ttk.Entry(filter_frame)
        self.exclude_entry.insert(0, ", ".join(self.exclude_patterns))
        self.exclude_entry.pack(fill=tk.X)
        
        # 语言选择
        lang_frame = ttk.LabelFrame(parent, text="统计语言", padding=10)
        lang_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建滚动区域用于语言选择
        lang_canvas = tk.Canvas(lang_frame, highlightthickness=0)
        lang_scrollbar = ttk.Scrollbar(lang_frame, orient="vertical", command=lang_canvas.yview)
        self.lang_scroll_frame = ttk.Frame(lang_canvas)
        
        self.lang_scroll_frame.bind(
            "<Configure>",
            lambda e: lang_canvas.configure(scrollregion=lang_canvas.bbox("all"))
        )
        
        lang_canvas.create_window((0, 0), window=self.lang_scroll_frame, anchor="nw")
        lang_canvas.configure(yscrollcommand=lang_scrollbar.set)
        
        lang_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lang_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 语言选择复选框
        self.lang_vars = {}
        for lang in self.language_configs.keys():
            var = tk.BooleanVar(value=True)
            self.lang_vars[lang] = var
            cb = ttk.Checkbutton(self.lang_scroll_frame, text=lang, variable=var)
            cb.pack(anchor=tk.W, pady=2)
        
        # 自定义语言按钮
        ttk.Button(parent, text="自定义语言配置", command=self.custom_language_config).pack(fill=tk.X, pady=(0, 5))
        
        # 热重载配置按钮
        ttk.Button(parent, text="重新加载配置", command=self.reload_config).pack(fill=tk.X)
    
    def create_right_panel(self, parent):
        """创建右侧结果显示面板"""
        # 创建笔记本组件用于多个选项卡
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 统计结果选项卡
        result_frame = ttk.Frame(self.notebook)
        self.notebook.add(result_frame, text="统计结果")
        
        # 创建树状视图显示结果
        columns = ("语言", "文件数", "总行数", "代码行数", "注释行数", "空行数", "平均行数")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选中事件
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # 文件详情选项卡
        detail_frame = ttk.Frame(self.notebook)
        self.notebook.add(detail_frame, text="文件详情")
        
        # 文件详情文本区域
        self.detail_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=20)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 比较结果选项卡
        compare_frame = ttk.Frame(self.notebook)
        self.notebook.add(compare_frame, text="结果比较")
        
        # 比较结果文本区域
        self.compare_text = scrolledtext.ScrolledText(compare_frame, wrap=tk.WORD, height=20)
        self.compare_text.pack(fill=tk.BOTH, expand=True)
        
        # 汇总信息框架
        summary_frame = ttk.Frame(result_frame)
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 汇总标签
        self.summary_label = ttk.Label(summary_frame, text="等待统计...", font=("Segoe UI", 10))
        self.summary_label.pack(anchor=tk.W)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_bar = ttk.Frame(parent, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_bar, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(self.status_bar, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5)
    
    def bind_events(self):
        """绑定事件"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def apply_theme(self):
        """应用主题"""
        if self.is_dark_mode:
            bg = self.dark_bg
            fg = self.dark_fg
            select = self.dark_select
            accent = self.dark_accent
            hover = self.dark_hover
            active = self.dark_active
        else:
            bg = self.light_bg
            fg = self.light_fg
            select = self.light_select
            accent = self.light_accent
            hover = self.light_hover
            active = self.light_active
        
        # 更新主题按钮文本
        self.theme_btn.config(text=" ☀️ 浅色模式" if self.is_dark_mode else " 🌙 深色模式")
        
        # 配置样式
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TButton", 
                            background=select, 
                            foreground=fg,
                            borderwidth=1)
        
        # 配置按钮悬停状态
        self.style.map("TButton",
                      background=[('active', hover),
                                 ('pressed', active)],
                      foreground=[('active', fg),
                                 ('pressed', fg)])
        
        # 配置强调按钮
        self.style.configure("Accent.TButton", 
                            background=accent, 
                            foreground="white")
        self.style.map("Accent.TButton",
                      background=[('active', accent),
                                 ('pressed', accent)],
                      foreground=[('active', 'white'),
                                 ('pressed', 'white')])
        
        # 配置输入框
        self.style.configure("TEntry", 
                            fieldbackground=select, 
                            foreground=fg,
                            insertcolor=fg)
        
        # 配置复选框
        self.style.configure("TCheckbutton", 
                            background=bg, 
                            foreground=fg)
        
        # 配置笔记本
        self.style.configure("TNotebook", background=bg)
        self.style.configure("TNotebook.Tab", 
                            background=select, 
                            foreground=fg,
                            padding=[10, 5])
        self.style.map("TNotebook.Tab", 
                      background=[("selected", bg)],
                      foreground=[("selected", fg)])
        
        # 配置滚动条
        self.style.configure("Vertical.TScrollbar", 
                            background=select,
                            troughcolor=bg,
                            bordercolor=bg,
                            arrowcolor=fg)
        
        # 配置进度条
        self.style.configure("Horizontal.TProgressbar",
                            background=accent,
                            troughcolor=select,
                            bordercolor=select,
                            lightcolor=accent,
                            darkcolor=accent)
        
        # 重新配置树状视图
        self.configure_treeview_style(bg, fg, select, accent)
        
        # 配置滚动文本框
        self.detail_text.configure(bg=select, fg=fg, insertbackground=fg)
        self.compare_text.configure(bg=select, fg=fg, insertbackground=fg)
        
        # 配置根窗口
        self.root.configure(bg=bg)
        
        # 更新所有子控件
        self.update_widget_colors(self.root, bg, fg)
        
        # 强制更新树状视图
        self.tree.configure(style="Custom.Treeview")
    
    def configure_treeview_style(self, bg, fg, select, accent):
        """配置树状视图样式"""
        # 创建自定义树状视图样式
        self.style.element_create("Custom.Treeheading.border", "from", "clam")
        self.style.layout("Custom.Treeview", [
            ('Custom.Treeview.treearea', {'sticky': 'nswe'})
        ])
        
        # 配置树状视图
        self.style.configure("Custom.Treeview",
                            background=select,
                            foreground=fg,
                            fieldbackground=select,
                            borderwidth=0)
        
        # 配置树状视图标题
        self.style.configure("Custom.Treeview.Heading",
                            background=select,
                            foreground=fg,
                            relief="flat",
                            borderwidth=1)
        
        # 配置树状视图选中状态
        self.style.map("Custom.Treeview",
                      background=[('selected', accent)],
                      foreground=[('selected', 'white')])
        
        # 配置树状视图标题悬停状态
        self.style.map("Custom.Treeview.Heading",
                      background=[('active', select)])
    
    def update_widget_colors(self, widget, bg, fg):
        """递归更新控件颜色"""
        try:
            if isinstance(widget, tk.Text) or isinstance(widget, scrolledtext.ScrolledText):
                widget.configure(bg=bg, fg=fg, insertbackground=fg)
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=bg, highlightbackground=bg)
            elif hasattr(widget, 'configure'):
                # 尝试配置背景和前景色
                try:
                    widget.configure(bg=bg, fg=fg)
                except:
                    pass
        except:
            pass
        
        for child in widget.winfo_children():
            self.update_widget_colors(child, bg, fg)
    
    def toggle_theme(self):
        """切换主题"""
        self.is_dark_mode = not self.is_dark_mode
        self.config["dark_mode"] = self.is_dark_mode
        self.save_config()
        self.apply_theme()
        
        # 刷新树状视图以清除残留颜色
        self.refresh_treeview()
    
    def refresh_treeview(self):
        """刷新树状视图"""
        # 获取当前所有项
        items = self.tree.get_children()
        if items:
            # 暂时移除所有项
            for item in items:
                self.tree.delete(item)
            
            # 如果有结果数据，重新添加
            if self.results:
                self.update_results_ui()
    
    def load_config(self):
        """加载配置"""
        config_path = "code_counter_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_config()
        return self.get_default_config()
    
    def save_config(self):
        """保存配置"""
        config_path = "code_counter_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "dark_mode": True,
            "language_configs": CodeAnalyzer.DEFAULT_LANGUAGES,
            "include_patterns": ["*"],
            "exclude_patterns": [],
            "recent_directories": []
        }
    
    def load_custom_language_configs(self):
        """加载自定义语言配置"""
        custom_config_path = "custom_languages.json"
        if os.path.exists(custom_config_path):
            try:
                with open(custom_config_path, 'r', encoding='utf-8') as f:
                    custom_configs = json.load(f)
                    self.language_configs.update(custom_configs)
                    
                    # 更新语言选择复选框
                    for lang in custom_configs.keys():
                        if lang not in self.lang_vars:
                            var = tk.BooleanVar(value=True)
                            self.lang_vars[lang] = var
                            cb = ttk.Checkbutton(self.lang_scroll_frame, text=lang, variable=var)
                            cb.pack(anchor=tk.W, pady=2)
            except Exception as e:
                print(f"加载自定义语言配置失败: {e}")
    
    def select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(title="选择代码目录")
        if directory:
            self.current_directory = directory
            self.dir_label.config(text=f"目录: {directory}")
            
            # 添加到最近目录
            if directory in self.config.get("recent_directories", []):
                self.config["recent_directories"].remove(directory)
            self.config["recent_directories"].insert(0, directory)
            self.config["recent_directories"] = self.config["recent_directories"][:10]
            self.save_config()
    
    def start_analysis(self):
        """开始分析"""
        if not self.current_directory:
            messagebox.showwarning("警告", "请先选择目录")
            return
        
        # 更新配置
        self.update_config_from_ui()
        
        # 清空结果
        self.results = {}
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.detail_text.delete(1.0, tk.END)
        
        # 开始分析线程
        self.analysis_thread = threading.Thread(target=self.analyze_directory, daemon=True)
        self.analysis_thread.start()
        
        # 显示进度条
        self.progress.start()
        self.status_label.config(text="分析中...")
    
    def update_config_from_ui(self):
        """从UI更新配置"""
        # 获取包含/排除模式
        include_text = self.include_entry.get()
        exclude_text = self.exclude_entry.get()
        
        self.include_patterns = [p.strip() for p in include_text.split(",") if p.strip()]
        self.exclude_patterns = [p.strip() for p in exclude_text.split(",") if p.strip()]
        
        # 更新配置
        self.config["include_patterns"] = self.include_patterns
        self.config["exclude_patterns"] = self.exclude_patterns
        self.save_config()
        
        # 获取选中的语言
        selected_languages = [lang for lang, var in self.lang_vars.items() if var.get()]
        self.selected_languages = selected_languages
    
    def analyze_directory(self):
        """分析目录"""
        try:
            # 收集文件
            files = self.collect_files()
            
            # 分析每个文件
            for i, file_path in enumerate(files):
                # 获取文件语言
                language = CodeAnalyzer.get_language_from_extension(file_path, self.language_configs)
                
                # 如果语言不在选中的语言中，跳过
                if language not in self.selected_languages and language != "Unknown":
                    continue
                
                # 分析文件
                result = CodeAnalyzer.analyze_file(file_path, self.language_configs.get(language, {}))
                
                if result:
                    # 添加到结果
                    if language not in self.results:
                        self.results[language] = {
                            "files": [],
                            "total_lines": 0,
                            "code_lines": 0,
                            "comment_lines": 0,
                            "empty_lines": 0
                        }
                    
                    self.results[language]["files"].append(result)
                    self.results[language]["total_lines"] += result["total_lines"]
                    self.results[language]["code_lines"] += result["code_lines"]
                    self.results[language]["comment_lines"] += result["comment_lines"]
                    self.results[language]["empty_lines"] += result["empty_lines"]
                
                # 每处理10个文件更新一次UI
                if i % 10 == 0:
                    self.root.after(0, self.update_results_ui)
            
            # 最终更新UI
            self.root.after(0, self.finish_analysis)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"分析失败: {str(e)}"))
            self.root.after(0, self.stop_progress)
    
    def collect_files(self):
        """收集文件"""
        files = []
        
        for root_dir, dirs, filenames in os.walk(self.current_directory):
            # 排除隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                file_path = os.path.join(root_dir, filename)
                
                # 检查是否匹配排除模式
                skip = False
                for pattern in self.exclude_patterns:
                    if pattern and pattern != "*" and pattern in file_path:
                        skip = True
                        break
                
                if skip:
                    continue
                
                # 检查是否匹配包含模式
                include = False
                if "*" in self.include_patterns:
                    include = True
                else:
                    for pattern in self.include_patterns:
                        if pattern and pattern in file_path:
                            include = True
                            break
                
                if include:
                    files.append(file_path)
        
        return files
    
    def update_results_ui(self):
        """更新结果UI"""
        # 清空树状视图
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加结果
        total_files = 0
        total_lines = 0
        total_code = 0
        total_comment = 0
        total_empty = 0
        
        for language, data in self.results.items():
            file_count = len(data["files"])
            total_lines_lang = data["total_lines"]
            code_lines_lang = data["code_lines"]
            comment_lines_lang = data["comment_lines"]
            empty_lines_lang = data["empty_lines"]
            
            # 计算平均行数
            avg_lines = code_lines_lang / file_count if file_count > 0 else 0
            
            # 添加到树状视图
            self.tree.insert("", "end", values=(
                language,
                file_count,
                total_lines_lang,
                code_lines_lang,
                comment_lines_lang,
                empty_lines_lang,
                f"{avg_lines:.1f}"
            ))
            
            # 更新总计
            total_files += file_count
            total_lines += total_lines_lang
            total_code += code_lines_lang
            total_comment += comment_lines_lang
            total_empty += empty_lines_lang
        
        # 更新汇总信息
        summary_text = f"总计: {total_files} 个文件, {total_lines} 行代码 (净代码: {total_code}, 注释: {total_comment}, 空行: {total_empty})"
        self.summary_label.config(text=summary_text)
    
    def finish_analysis(self):
        """完成分析"""
        self.update_results_ui()
        self.stop_progress()
        self.status_label.config(text=f"分析完成，共处理 {sum(len(data['files']) for data in self.results.values())} 个文件")
        
        # 显示文件详情
        self.update_detail_text()
    
    def stop_progress(self):
        """停止进度条"""
        self.progress.stop()
    
    def stop_analysis(self):
        """停止分析"""
        # 由于分析在后台线程运行，我们只能设置一个标志
        # 在实际应用中，可能需要更复杂的线程控制
        self.status_label.config(text="分析已停止")
        self.stop_progress()
    
    def update_detail_text(self):
        """更新文件详情文本"""
        self.detail_text.delete(1.0, tk.END)
        
        for language, data in self.results.items():
            self.detail_text.insert(tk.END, f"\n{language}:\n", "title")
            self.detail_text.insert(tk.END, "=" * 40 + "\n")
            
            for file_data in data["files"]:
                self.detail_text.insert(tk.END, 
                    f"{file_data['file_name']}: "
                    f"总行={file_data['total_lines']}, "
                    f"代码={file_data['code_lines']}, "
                    f"注释={file_data['comment_lines']}, "
                    f"空行={file_data['empty_lines']}\n"
                )
            
            self.detail_text.insert(tk.END, "\n")
        
        # 添加样式标签
        self.detail_text.tag_configure("title", font=("Segoe UI", 10, "bold"))
    
    def on_tree_select(self, event):
        """树状视图选择事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            language = item["values"][0]
            
            # 显示选中语言的详细信息
            self.show_language_details(language)
    
    def show_language_details(self, language):
        """显示语言详细信息"""
        if language in self.results:
            data = self.results[language]
            
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"{language} 详细信息")
            detail_window.geometry("800x600")
            
            # 应用主题
            if self.is_dark_mode:
                bg = self.dark_bg
                fg = self.dark_fg
                select = self.dark_select
            else:
                bg = self.light_bg
                fg = self.light_fg
                select = self.light_select
            
            detail_window.configure(bg=bg)
            
            # 创建文本区域
            text_area = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 应用主题到文本区域
            text_area.configure(bg=select, fg=fg, insertbackground=fg)
            
            # 添加内容
            text_area.insert(tk.END, f"{language} 代码统计详情\n", "title")
            text_area.insert(tk.END, "=" * 50 + "\n\n")
            
            text_area.insert(tk.END, f"文件数量: {len(data['files'])}\n")
            text_area.insert(tk.END, f"总行数: {data['total_lines']}\n")
            text_area.insert(tk.END, f"代码行数: {data['code_lines']}\n")
            text_area.insert(tk.END, f"注释行数: {data['comment_lines']}\n")
            text_area.insert(tk.END, f"空行数: {data['empty_lines']}\n\n")
            
            text_area.insert(tk.END, "文件列表:\n", "subtitle")
            for file_data in data["files"]:
                text_area.insert(tk.END, f"\n{file_data['file_path']}\n", "filepath")
                text_area.insert(tk.END, 
                    f"  总行: {file_data['total_lines']}, "
                    f"代码: {file_data['code_lines']}, "
                    f"注释: {file_data['comment_lines']}, "
                    f"空行: {file_data['empty_lines']}\n"
                )
            
            # 配置标签样式
            text_area.tag_configure("title", font=("Segoe UI", 14, "bold"))
            text_area.tag_configure("subtitle", font=("Segoe UI", 12, "bold"))
            text_area.tag_configure("filepath", font=("Segoe UI", 10, "italic"))
            
            # 禁用编辑
            text_area.configure(state=tk.DISABLED)
    
    def export_results(self):
        """导出结果"""
        if not self.results:
            messagebox.showwarning("警告", "没有可导出的结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="导出结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                export_data = {
                    "directory": self.current_directory,
                    "timestamp": datetime.now().isoformat(),
                    "results": self.results,
                    "config": {
                        "include_patterns": self.include_patterns,
                        "exclude_patterns": self.exclude_patterns,
                        "selected_languages": self.selected_languages
                    }
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("成功", f"结果已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def import_results(self):
        """导入结果"""
        file_path = filedialog.askopenfilename(
            title="导入结果",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                self.results = import_data.get("results", {})
                self.update_results_ui()
                self.update_detail_text()
                
                messagebox.showinfo("成功", "结果已导入")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def compare_results(self):
        """比较结果"""
        # 要求用户选择两个结果文件进行比较
        file1 = filedialog.askopenfilename(
            title="选择第一个结果文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file1:
            return
        
        file2 = filedialog.askopenfilename(
            title="选择第二个结果文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file2:
            return
        
        try:
            # 加载结果文件
            with open(file1, 'r', encoding='utf-8') as f:
                data1 = json.load(f)
            
            with open(file2, 'r', encoding='utf-8') as f:
                data2 = json.load(f)
            
            # 比较结果
            self.perform_comparison(data1, data2)
            
            # 切换到比较选项卡
            self.notebook.select(2)
            
        except Exception as e:
            messagebox.showerror("错误", f"比较失败: {str(e)}")
    
    def perform_comparison(self, data1, data2):
        """执行比较"""
        results1 = data1.get("results", {})
        results2 = data2.get("results", {})
        
        # 清空比较文本区域
        self.compare_text.delete(1.0, tk.END)
        
        # 添加标题
        self.compare_text.insert(tk.END, "代码统计结果比较\n", "title")
        self.compare_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # 比较总体统计
        self.compare_text.insert(tk.END, "总体统计:\n", "subtitle")
        
        total_files1 = sum(len(data["files"]) for data in results1.values())
        total_files2 = sum(len(data["files"]) for data in results2.values())
        files_diff = total_files2 - total_files1
        
        total_lines1 = sum(data["total_lines"] for data in results1.values())
        total_lines2 = sum(data["total_lines"] for data in results2.values())
        lines_diff = total_lines2 - total_lines1
        
        self.compare_text.insert(tk.END, f"文件数量: {total_files1} → {total_files2} ({files_diff:+d})\n")
        self.compare_text.insert(tk.END, f"总行数: {total_lines1} → {total_lines2} ({lines_diff:+d})\n\n")
        
        # 比较每种语言
        all_languages = set(results1.keys()) | set(results2.keys())
        
        for language in sorted(all_languages):
            self.compare_text.insert(tk.END, f"{language}:\n", "language")
            
            data1 = results1.get(language, {"files": [], "total_lines": 0, "code_lines": 0})
            data2 = results2.get(language, {"files": [], "total_lines": 0, "code_lines": 0})
            
            files1 = len(data1["files"])
            files2 = len(data2["files"])
            files_diff = files2 - files1
            
            lines1 = data1["total_lines"]
            lines2 = data2["total_lines"]
            lines_diff = lines2 - lines1
            
            code1 = data1.get("code_lines", 0)
            code2 = data2.get("code_lines", 0)
            code_diff = code2 - code1
            
            self.compare_text.insert(tk.END, 
                f"  文件: {files1} → {files2} ({files_diff:+d})\n"
                f"  总行: {lines1} → {lines2} ({lines_diff:+d})\n"
                f"  代码: {code1} → {code2} ({code_diff:+d})\n\n"
            )
        
        # 配置标签样式
        self.compare_text.tag_configure("title", font=("Segoe UI", 14, "bold"))
        self.compare_text.tag_configure("subtitle", font=("Segoe UI", 12, "bold"))
        self.compare_text.tag_configure("language", font=("Segoe UI", 11, "bold"))
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("600x500")
        
        # 应用主题
        if self.is_dark_mode:
            bg = self.dark_bg
            fg = self.dark_fg
            select = self.dark_select
        else:
            bg = self.light_bg
            fg = self.light_fg
            select = self.light_select
        
        settings_window.configure(bg=bg)
        
        # 创建笔记本
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 常规设置
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="常规")
        
        # 语言配置
        lang_config_frame = ttk.Frame(notebook)
        notebook.add(lang_config_frame, text="语言配置")
        
        # 填充常规设置
        self.create_general_settings(general_frame)
        
        # 填充语言配置
        self.create_language_settings(lang_config_frame)
    
    def create_general_settings(self, parent):
        """创建常规设置"""
        # 自动保存配置
        auto_save_var = tk.BooleanVar(value=self.config.get("auto_save", True))
        auto_save_cb = ttk.Checkbutton(parent, text="自动保存配置", variable=auto_save_var)
        auto_save_cb.pack(anchor=tk.W, pady=5, padx=10)
        
        # 默认包含模式
        ttk.Label(parent, text="默认包含模式:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        default_include_entry = ttk.Entry(parent, width=50)
        default_include_entry.insert(0, ", ".join(self.config.get("default_include", ["*"])))
        default_include_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # 保存按钮
        def save_general_settings():
            self.config["auto_save"] = auto_save_var.get()
            self.config["default_include"] = [p.strip() for p in default_include_entry.get().split(",") if p.strip()]
            self.save_config()
            messagebox.showinfo("成功", "设置已保存")
        
        ttk.Button(parent, text="保存设置", command=save_general_settings).pack(pady=20)
    
    def create_language_settings(self, parent):
        """创建语言配置"""
        # 创建滚动区域
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加语言配置
        for lang, config in self.language_configs.items():
            lang_frame = ttk.LabelFrame(scroll_frame, text=lang, padding=10)
            lang_frame.pack(fill=tk.X, pady=5, padx=10)
            
            # 扩展名
            ttk.Label(lang_frame, text="扩展名:").grid(row=0, column=0, sticky=tk.W, pady=2)
            ext_entry = ttk.Entry(lang_frame, width=40)
            ext_entry.insert(0, ", ".join(config.get("extensions", [])))
            ext_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
            
            # 单行注释
            ttk.Label(lang_frame, text="单行注释:").grid(row=1, column=0, sticky=tk.W, pady=2)
            single_comment_entry = ttk.Entry(lang_frame, width=40)
            single_comments = config.get("single_line_comment", [])
            if isinstance(single_comments, list):
                single_comment_entry.insert(0, ", ".join(single_comments))
            else:
                single_comment_entry.insert(0, single_comments)
            single_comment_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 添加新语言按钮
        def add_new_language():
            new_lang_window = tk.Toplevel(parent)
            new_lang_window.title("添加新语言")
            new_lang_window.geometry("400x300")
            
            # 应用主题
            if self.is_dark_mode:
                bg = self.dark_bg
                fg = self.dark_fg
            else:
                bg = self.light_bg
                fg = self.light_fg
            
            new_lang_window.configure(bg=bg)
            
            ttk.Label(new_lang_window, text="语言名称:").pack(pady=(10, 0))
            name_entry = ttk.Entry(new_lang_window, width=30)
            name_entry.pack(pady=5)
            
            ttk.Label(new_lang_window, text="扩展名 (用逗号分隔):").pack(pady=(10, 0))
            ext_entry = ttk.Entry(new_lang_window, width=30)
            ext_entry.pack(pady=5)
            
            ttk.Label(new_lang_window, text="单行注释符号:").pack(pady=(10, 0))
            comment_entry = ttk.Entry(new_lang_window, width=30)
            comment_entry.pack(pady=5)
            
            def save_new_language():
                name = name_entry.get().strip()
                if not name:
                    messagebox.showwarning("警告", "请输入语言名称")
                    return
                
                extensions = [ext.strip() for ext in ext_entry.get().split(",") if ext.strip()]
                comments = [c.strip() for c in comment_entry.get().split(",") if c.strip()]
                
                # 添加到配置
                self.language_configs[name] = {
                    "extensions": extensions,
                    "single_line_comment": comments[0] if len(comments) == 1 else comments,
                    "multi_line_comment": [],
                    "string_delimiters": ['"', "'"]
                }
                
                # 保存配置
                self.config["language_configs"] = self.language_configs
                self.save_config()
                
                # 更新UI
                if name not in self.lang_vars:
                    var = tk.BooleanVar(value=True)
                    self.lang_vars[name] = var
                    cb = ttk.Checkbutton(self.lang_scroll_frame, text=name, variable=var)
                    cb.pack(anchor=tk.W, pady=2)
                
                messagebox.showinfo("成功", f"语言 {name} 已添加")
                new_lang_window.destroy()
            
            ttk.Button(new_lang_window, text="保存", command=save_new_language).pack(pady=20)
        
        ttk.Button(scroll_frame, text="添加新语言", command=add_new_language).pack(pady=10)
    
    def custom_language_config(self):
        """自定义语言配置"""
        config_window = tk.Toplevel(self.root)
        config_window.title("自定义语言配置")
        config_window.geometry("500x400")
        
        # 应用主题
        if self.is_dark_mode:
            bg = self.dark_bg
            fg = self.dark_fg
            select = self.dark_select
        else:
            bg = self.light_bg
            fg = self.light_fg
            select = self.light_select
        
        config_window.configure(bg=bg)
        
        # 创建文本编辑器
        text_area = scrolledtext.ScrolledText(config_window, wrap=tk.WORD, height=20)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 应用主题到文本区域
        text_area.configure(bg=select, fg=fg, insertbackground=fg)
        
        # 加载当前配置
        custom_config_path = "custom_languages.json"
        if os.path.exists(custom_config_path):
            try:
                with open(custom_config_path, 'r', encoding='utf-8') as f:
                    content = json.dumps(json.load(f), indent=2, ensure_ascii=False)
                    text_area.insert(1.0, content)
            except:
                text_area.insert(1.0, "{\n  \n}")
        else:
            text_area.insert(1.0, "{\n  \n}")
        
        def save_custom_config():
            try:
                content = text_area.get(1.0, tk.END)
                config = json.loads(content)
                
                with open("custom_languages.json", 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                # 重新加载配置
                self.load_custom_language_configs()
                
                messagebox.showinfo("成功", "自定义语言配置已保存")
                config_window.destroy()
            except json.JSONDecodeError as e:
                messagebox.showerror("错误", f"JSON格式错误: {str(e)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
        
        # 保存按钮
        ttk.Button(config_window, text="保存", command=save_custom_config).pack(pady=(0, 10))
    
    def reload_config(self):
        """重新加载配置"""
        self.config = self.load_config()
        self.language_configs = self.config.get("language_configs", CodeAnalyzer.DEFAULT_LANGUAGES)
        self.load_custom_language_configs()
        
        # 更新UI
        self.include_patterns = self.config.get("include_patterns", ["*"])
        self.exclude_patterns = self.config.get("exclude_patterns", [])
        
        self.include_entry.delete(0, tk.END)
        self.include_entry.insert(0, ", ".join(self.include_patterns))
        
        self.exclude_entry.delete(0, tk.END)
        self.exclude_entry.insert(0, ", ".join(self.exclude_patterns))
        
        messagebox.showinfo("成功", "配置已重新加载")
    
    def open_about(self):
        """打开关于窗口"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("500x450")  # 增加窗口大小
        
        # 应用主题
        if self.is_dark_mode:
            bg = self.dark_bg
            fg = self.dark_fg
            accent = self.dark_accent
        else:
            bg = self.light_bg
            fg = self.light_fg
            accent = self.light_accent
        
        about_window.configure(bg=bg)
        
        # 创建内容框架
        content_frame = tk.Frame(about_window, bg=bg)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            content_frame, 
            text="GetTotal", 
            font=("Segoe UI", 20, "bold"),
            bg=bg, fg=accent
        )
        title_label.pack(pady=(0, 10))
        
        # 版本信息
        version_label = tk.Label(
            content_frame, 
            text="版本 1.0.0",
            font=("Segoe UI", 12),
            bg=bg, fg=fg
        )
        version_label.pack(pady=(0, 20))
        
        # 创建可滚动的描述区域
        desc_frame = tk.Frame(content_frame, bg=bg)
        desc_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        desc_canvas = tk.Canvas(desc_frame, bg=bg, highlightthickness=0, height=200)
        scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=desc_canvas.yview)
        scrollable_frame = tk.Frame(desc_canvas, bg=bg)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: desc_canvas.configure(scrollregion=desc_canvas.bbox("all"))
        )
        
        desc_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        desc_canvas.configure(yscrollcommand=scrollbar.set)
        
        desc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 描述文本
        desc_text = """一个好用的代码统计工具，支持多种编程语言，具有高度可定制的配置选项。

功能特点：
• 支持多种编程语言
• 高度可配置的统计规则
• 深色/浅色主题切换
• 结果导出与比较
• 热重载配置
• 现代扁平化界面设计

技术支持：
• 使用Python 3.12.4开发
• 基于tkinter/ttk GUI框架
• 支持JSON格式配置导入导出

更新日志：
• 版本1.0.0 - 初始发布版本
• 修复深色模式颜色问题
• 优化主题切换体验
• 改进关于界面布局"""
        
        desc_label = tk.Label(
            scrollable_frame, 
            text=desc_text,
            justify=tk.LEFT,
            font=("Segoe UI", 10),
            bg=bg, fg=fg,
            wraplength=400  # 设置自动换行宽度
        )
        desc_label.pack(pady=(0, 20))
        
        # 作者链接
        link_frame = tk.Frame(scrollable_frame, bg=bg)
        link_frame.pack()
        
        tk.Label(link_frame, text="作者: ", bg=bg, fg=fg, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        # 创建可点击的链接
        link_label = tk.Label(
            link_frame, 
            text="Buelier", 
            fg=accent, 
            cursor="hand2",
            font=("Segoe UI", 10, "underline"),
            bg=bg
        )
        link_label.pack(side=tk.LEFT)
        
        def open_link(event):
            webbrowser.open("http://buelier.github.io")
        
        link_label.bind("<Button-1>", open_link)
        
        # 关闭按钮
        ttk.Button(content_frame, text="关闭", command=about_window.destroy).pack(pady=(20, 0))
    
    def on_closing(self):
        """关闭应用程序"""
        self.save_config()
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = ModernCodeCounterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
