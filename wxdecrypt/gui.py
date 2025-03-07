"""
GUI界面模块，提供图形用户界面操作
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import time
import platform
from typing import List, Dict, Any, Optional

# 导入其他模块
from wxdecrypt.wechat_path import get_wechat_db_path, get_qq_db_path
from wxdecrypt.db_decrypt import WeChatDBDecrypt
from wxdecrypt.utils.memory_utils import get_wechat_key  # 确保导入get_wechat_key函数

# 尝试导入真实解密模块
try:
    from wxdecrypt.real_decrypt import RealWeChatDBDecrypt
    HAS_REAL_DECRYPT = True
except ImportError:
    HAS_REAL_DECRYPT = False

# 导入数据分析模块（如果安装了相关依赖）
try:
    from wxdecrypt.data_analysis import generate_analysis_report
    HAS_ANALYSIS = True
except ImportError:
    HAS_ANALYSIS = False

class RedirectText:
    """重定向stdout到tkinter Text控件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.updating = True
        threading.Thread(target=self.update_text_widget, daemon=True).start()
        
    def write(self, string):
        self.queue.put(string)
        
    def flush(self):
        pass
        
    def update_text_widget(self):
        while self.updating:
            try:
                while True:
                    text = self.queue.get_nowait()
                    self.text_widget.configure(state="normal")
                    self.text_widget.insert(tk.END, text)
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state="disabled")
                    self.queue.task_done()
            except queue.Empty:
                pass
            time.sleep(0.1)
            
    def close(self):
        self.updating = False

class WxDecryptApp:
    """微信/QQ数据库解密工具GUI应用"""
    
    def __init__(self, root):
        """初始化应用"""
        self.root = root
        self.root.title("微信/QQ数据库解密工具")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 创建变量
        self.found_databases = []
        self.output_var = tk.StringVar(value="./output")
        self.search_var = tk.StringVar()
        self.drives_var = tk.StringVar()
        self.type_var = tk.StringVar(value="微信")
        self.full_scan_var = tk.BooleanVar(value=False)
        self.selected_dbs = []
        self.key = None
        self.status_var = tk.StringVar(value="就绪")
        self.analyzing = False
        self.last_report_path = None
        
        # 用于数据分析的变量
        self.db_path_var = tk.StringVar()
        self.db_type_var = tk.StringVar(value="微信")
        self.analysis_output_var = tk.StringVar(value="./output/analysis")
        
        # 真实解密选项
        self.use_real_decrypt_var = tk.BooleanVar(value=True if HAS_REAL_DECRYPT else False)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TNotebook", tabposition='n')
        self.style.configure("TButton", padding=6)
        
        # 创建标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各功能页面
        self.create_search_tab()
        self.create_decrypt_tab()
        if HAS_ANALYSIS:
            self.create_analysis_tab()
        
        # 状态栏
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_search_tab(self):
        """创建数据库搜索标签页"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="搜索数据库")
        
        # 控制区域
        control_frame = ttk.LabelFrame(search_frame, text="搜索选项")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 应用选项
        app_frame = ttk.Frame(control_frame)
        app_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(app_frame, text="应用类型:").pack(side=tk.LEFT, padx=5)
        self.app_var = tk.StringVar(value="微信")
        ttk.Radiobutton(app_frame, text="微信", variable=self.app_var, value="微信").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(app_frame, text="QQ", variable=self.app_var, value="QQ").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(app_frame, text="全部", variable=self.app_var, value="全部").pack(side=tk.LEFT, padx=5)
        
        # 搜索选项
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 驱动器选项
        ttk.Label(options_frame, text="搜索驱动器:").pack(side=tk.LEFT, padx=5)
        self.drive_var = tk.StringVar(value="自动")
        drives_combo = ttk.Combobox(options_frame, textvariable=self.drive_var, width=20)
        all_drives = self.get_available_drives()
        drives_combo['values'] = ["自动"] + all_drives
        drives_combo.pack(side=tk.LEFT, padx=5)
        
        # 全盘搜索
        self.full_scan_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="全盘搜索", variable=self.full_scan_var).pack(side=tk.LEFT, padx=20)
        
        # 按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="开始搜索", command=self.start_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除结果", command=self.clear_search_results).pack(side=tk.LEFT, padx=5)
        
        # 结果列表
        result_frame = ttk.LabelFrame(search_frame, text="搜索结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建表格
        columns = ('id', 'type', 'username', 'db_name', 'path')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.result_tree.heading('id', text='#')
        self.result_tree.heading('type', text='类型')
        self.result_tree.heading('username', text='用户名/QQ号')
        self.result_tree.heading('db_name', text='数据库名')
        self.result_tree.heading('path', text='路径')
        
        # 设置列宽
        self.result_tree.column('id', width=30, stretch=tk.NO)
        self.result_tree.column('type', width=60, stretch=tk.NO)
        self.result_tree.column('username', width=120, stretch=tk.NO)
        self.result_tree.column('db_name', width=120, stretch=tk.NO)
        self.result_tree.column('path', width=450)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscroll=scrollbar.set)
        
        # 放置控件
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.result_tree.bind("<Double-1>", self.on_db_double_click)
        
    def create_decrypt_tab(self):
        """创建解密标签页"""
        decrypt_frame = ttk.Frame(self.notebook)
        self.notebook.add(decrypt_frame, text="解密数据库")
        
        # 控制区域
        control_frame = ttk.LabelFrame(decrypt_frame, text="解密选项")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 输出目录选择
        path_frame = ttk.Frame(control_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_frame, text="输出目录:").pack(side=tk.LEFT, padx=5)
        self.output_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
        output_entry = ttk.Entry(path_frame, textvariable=self.output_path_var, width=50)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览...", command=self.browse_output_dir).pack(side=tk.LEFT, padx=5)
        
        # 数据分析选项
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.analyze_var = tk.BooleanVar(value=HAS_ANALYSIS)
        analyze_check = ttk.Checkbutton(options_frame, text="解密后进行数据分析", variable=self.analyze_var)
        analyze_check.pack(side=tk.LEFT, padx=5)
        if not HAS_ANALYSIS:
            analyze_check.configure(state="disabled")
            ttk.Label(options_frame, text="(需安装分析依赖)").pack(side=tk.LEFT)
        
        # 真实解密选项
        decrypt_mode_frame = ttk.Frame(control_frame)
        decrypt_mode_frame.pack(fill=tk.X, padx=10, pady=5, anchor=tk.W)
        
        if HAS_REAL_DECRYPT:
            ttk.Checkbutton(decrypt_mode_frame, text="使用真实解密（基于PyWxDump，推荐）", 
                          variable=self.use_real_decrypt_var).pack(side=tk.LEFT)
        else:
            ttk.Label(decrypt_mode_frame, text="真实解密模块未安装，将使用基本解密").pack(side=tk.LEFT)
            ttk.Label(decrypt_mode_frame, text="可通过pip install PyWxDump安装").pack(side=tk.LEFT, padx=(10, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="开始解密", command=self.start_decrypt).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除日志", command=self.clear_decrypt_log).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(decrypt_frame, text="解密日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state="disabled", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 重定向stdout到日志窗口
        self.text_redirector = RedirectText(self.log_text)
        
    def create_analysis_tab(self):
        """创建数据分析标签页"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="数据分析")
        
        # 控制区域
        control_frame = ttk.LabelFrame(analysis_frame, text="分析选项")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 数据库选择
        db_frame = ttk.Frame(control_frame)
        db_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(db_frame, text="数据库路径:").pack(side=tk.LEFT, padx=5)
        self.db_path_var = tk.StringVar()
        db_entry = ttk.Entry(db_frame, textvariable=self.db_path_var, width=50)
        db_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(db_frame, text="浏览...", command=self.browse_db_file).pack(side=tk.LEFT, padx=5)
        
        # 数据库类型
        type_frame = ttk.Frame(control_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="数据库类型:").pack(side=tk.LEFT, padx=5)
        self.db_type_var = tk.StringVar(value="微信")
        ttk.Radiobutton(type_frame, text="微信", variable=self.db_type_var, value="微信").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="QQ", variable=self.db_type_var, value="QQ").pack(side=tk.LEFT, padx=5)
        
        # 按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="开始分析", command=self.start_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看报告", command=self.view_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除日志", command=self.clear_analysis_log).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(analysis_frame, text="分析日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.analysis_log_text = scrolledtext.ScrolledText(log_frame, state="disabled", wrap=tk.WORD)
        self.analysis_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 重定向用分析日志的变量
        self.analysis_redirector = None
        self.last_report_path = None
    
    def start_search(self):
        """开始搜索数据库"""
        self.status_var.set("正在搜索数据库...")
        self.found_databases = []
        
        # 清空结果表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 获取搜索参数
        app_type = self.app_var.get()
        drive = self.drive_var.get()
        full_scan = self.full_scan_var.get()
        
        # 处理搜索驱动器
        search_drives = None
        if drive != "自动":
            search_drives = [drive]
        
        # 开始搜索线程
        threading.Thread(target=self._search_thread, args=(app_type, search_drives, full_scan), daemon=True).start()
    
    def _search_thread(self, app_type, search_drives, full_scan):
        """搜索线程"""
        try:
            if app_type in ["微信", "全部"]:
                # 搜索微信数据库
                wechat_dbs = get_wechat_db_path(search_drives) if full_scan or search_drives else get_wechat_db_path()
                for db in wechat_dbs:
                    db['type'] = "微信"
                self.found_databases.extend(wechat_dbs)
            
            if app_type in ["QQ", "全部"]:
                # 搜索QQ数据库
                qq_dbs = get_qq_db_path(search_drives) if full_scan or search_drives else get_qq_db_path()
                for db in qq_dbs:
                    db['type'] = "QQ"
                self.found_databases.extend(qq_dbs)
            
            # 更新界面
            self.root.after(0, self._update_search_results)
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"搜索时出错: {e}"))
            self.root.after(0, lambda: self.status_var.set("搜索出错"))
    
    def _update_search_results(self):
        """更新搜索结果列表"""
        for idx, db in enumerate(self.found_databases, 1):
            db_type = db.get('type', 'unknown')
            
            if db_type == "微信":
                username = db.get('username', 'unknown')
                is_main = db.get('is_main_db', False)
                username_display = f"{username} {'(主)' if is_main else ''}"
            else:  # QQ
                username = db.get('qqid', 'unknown')
                username_display = username
            
            db_name = db.get('db_name', 'unknown')
            path = db.get('path', 'unknown')
            
            # 插入到表格
            self.result_tree.insert('', 'end', values=(idx, db_type, username_display, db_name, path))
        
        count = len(self.found_databases)
        self.status_var.set(f"搜索完成，找到 {count} 个数据库")
    
    def clear_search_results(self):
        """清除搜索结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.found_databases = []
        self.status_var.set("搜索结果已清除")
    
    def on_db_double_click(self, event):
        """双击数据库条目"""
        item = self.result_tree.selection()[0]
        values = self.result_tree.item(item, 'values')
        idx = int(values[0]) - 1
        
        if idx < len(self.found_databases):
            db = self.found_databases[idx]
            # 如果是在解密标签页，则自动填充到解密选项
            self.notebook.select(1)  # 切换到解密标签页
            
            # 确认是否解密
            if messagebox.askyesno("确认解密", f"是否解密选中的数据库?\n{db.get('path', '')}"):
                # 开始解密该数据库
                self._decrypt_selected_database(db)
    
    def _decrypt_selected_database(self, db):
        """解密选中的数据库"""
        output_dir = self.output_path_var.get()
        analyze = self.analyze_var.get()
        
        # 重定向stdout
        orig_stdout = sys.stdout
        sys.stdout = self.text_redirector
        
        threading.Thread(target=self._decrypt_thread, args=(db, output_dir, analyze, orig_stdout), daemon=True).start()
    
    def start_decrypt(self):
        """开始解密所有找到的数据库"""
        if not self.found_databases:
            messagebox.showinfo("提示", "没有找到数据库，请先搜索")
            self.notebook.select(0)  # 切换到搜索标签页
            return
        
        output_dir = self.output_path_var.get()
        analyze = self.analyze_var.get()
        
        # 确认是否解密
        if messagebox.askyesno("确认解密", f"是否解密所有找到的 {len(self.found_databases)} 个数据库?"):
            # 重定向stdout
            orig_stdout = sys.stdout
            sys.stdout = self.text_redirector
            
            threading.Thread(target=self._decrypt_all_thread, args=(output_dir, analyze, orig_stdout), daemon=True).start()
    
    def _decrypt_thread(self, db, output_dir, analyze, orig_stdout):
        """单个数据库解密线程"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在解密数据库..."))
            
            db_type = db.get('type', '')
            is_qq = (db_type == "QQ")
            
            # 使用真实解密模式
            use_real_decrypt = False
            if hasattr(self, 'use_real_decrypt_var') and hasattr(self.use_real_decrypt_var, 'get'):
                use_real_decrypt = HAS_REAL_DECRYPT and self.use_real_decrypt_var.get()
            
            # 选择解密器
            if use_real_decrypt:
                print("使用真实解密模块（基于PyWxDump）...")
                decryptor = RealWeChatDBDecrypt()
            else:
                decryptor = WeChatDBDecrypt()
            
            decryptor.decrypt_qq = is_qq
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 确定用户ID和应用名称
            if is_qq:
                user_id = db.get('qqid', 'unknown')
                app_name = "QQ"
            else:
                user_id = db.get('username', 'unknown')
                app_name = "WeChat"
            
            # 创建用户输出目录
            user_output_dir = os.path.join(output_dir, app_name, user_id)
            os.makedirs(user_output_dir, exist_ok=True)
            
            # 解密数据库
            db_path = db.get('path', '')
            db_name = db.get('db_name', '')
            output_path = os.path.join(user_output_dir, db_name)
            
            print(f"开始解密数据库: {db_path}")
            print(f"输出路径: {output_path}")
            
            # 获取密钥（如果需要）
            if not is_qq:
                if use_real_decrypt:
                    try:
                        # 使用PyWxDump获取真实密钥
                        from PyWxDump.wx import get_key as wx_get_key
                        key = wx_get_key()
                        if not key:
                            print("未能通过PyWxDump获取微信密钥，尝试备用方法...")
                            key = get_wechat_key()
                    except Exception as e:
                        print(f"使用PyWxDump获取密钥失败: {e}")
                        print("使用备用方法...")
                        key = get_wechat_key()
                
                self.key = decryptor.key = key
                if not decryptor.key:
                    print("未能获取微信数据库密钥")
                    self.root.after(0, lambda: self.status_var.set("解密失败"))
                    sys.stdout = orig_stdout
                    return
            
            # 解密
            success = decryptor.decrypt_db(db_path, output_path)
            
            if success:
                print(f"解密成功: {output_path}")
                self.root.after(0, lambda: self.status_var.set("解密成功"))
                
                # 如果需要分析
                if analyze and HAS_ANALYSIS:
                    print(f"开始分析数据库: {output_path}")
                    analysis_dir = os.path.join(os.path.dirname(output_path), 'analysis')
                    os.makedirs(analysis_dir, exist_ok=True)
                    
                    try:
                        report_path = generate_analysis_report(output_path, analysis_dir, is_qq)
                        print(f"分析完成! 报告保存到: {report_path}")
                        self.last_report_path = report_path
                    except Exception as e:
                        print(f"分析数据库时出错: {e}")
            else:
                print(f"解密失败: {db_path}")
                self.root.after(0, lambda: self.status_var.set("解密失败"))
        
        except Exception as e:
            print(f"解密过程出错: {e}")
            self.root.after(0, lambda: self.status_var.set("解密出错"))
        
        finally:
            # 恢复stdout
            sys.stdout = orig_stdout
            self.redirector = None
    
    def _decrypt_all_thread(self, output_dir, analyze, orig_stdout):
        """所有数据库解密线程"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在解密所有数据库..."))
            
            # 检查是否使用真实解密
            use_real_decrypt = False
            if hasattr(self, 'use_real_decrypt_var') and hasattr(self.use_real_decrypt_var, 'get'):
                use_real_decrypt = HAS_REAL_DECRYPT and self.use_real_decrypt_var.get()
            
            # 选择解密器
            if use_real_decrypt:
                print("使用真实解密模块（基于PyWxDump）...")
                wechat_decryptor = RealWeChatDBDecrypt()
                qq_decryptor = RealWeChatDBDecrypt()
            else:
                wechat_decryptor = WeChatDBDecrypt()
                qq_decryptor = WeChatDBDecrypt()
            
            # 设置QQ解密器
            qq_decryptor.decrypt_qq = True
            
            # 获取微信密钥
            wechat_dbs = [db for db in self.found_databases if db.get('type', '') == "微信"]
            if wechat_dbs:
                if use_real_decrypt:
                    try:
                        # 使用PyWxDump获取真实密钥
                        from PyWxDump.wx import get_key as wx_get_key
                        key = wx_get_key()
                        if not key:
                            print("未能通过PyWxDump获取微信密钥，尝试备用方法...")
                            key = get_wechat_key()
                    except Exception as e:
                        print(f"使用PyWxDump获取密钥失败: {e}")
                        print("尝试使用备用方法...")
                        key = get_wechat_key()
                else:
                    key = get_wechat_key()  # 直接调用导入的函数
                
                wechat_decryptor.key = key
                if not wechat_decryptor.key:
                    print("未能获取微信数据库密钥，将跳过微信数据库解密")
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 解密所有数据库
            success_count = 0
            for db in self.found_databases:
                db_type = db.get('type', '')
                is_qq = (db_type == "QQ")
                
                # 确定用户ID和应用名称
                if is_qq:
                    user_id = db.get('qqid', 'unknown')
                    app_name = "QQ"
                    decryptor = qq_decryptor
                else:
                    user_id = db.get('username', 'unknown')
                    app_name = "WeChat"
                    decryptor = wechat_decryptor
                
                # 创建用户输出目录
                user_output_dir = os.path.join(output_dir, app_name, user_id)
                os.makedirs(user_output_dir, exist_ok=True)
                
                # 解密数据库
                db_path = db.get('path', '')
                db_name = db.get('db_name', '')
                output_path = os.path.join(user_output_dir, db_name)
                
                print(f"解密数据库 ({db_type}): {db_path}")
                
                # 解密
                if not is_qq and not wechat_decryptor.key:
                    print("跳过，未获取到微信密钥")
                    continue
                
                success = decryptor.decrypt_db(db_path, output_path)
                
                if success:
                    success_count += 1
                    print(f"解密成功: {output_path}")
                    
                    # 如果需要分析
                    if analyze and HAS_ANALYSIS:
                        # 仅分析主数据库或消息数据库
                        is_main = db.get('is_main_db', False)
                        if is_main or 'msg' in db_name.lower():
                            analysis_dir = os.path.join(os.path.dirname(output_path), 'analysis')
                            os.makedirs(analysis_dir, exist_ok=True)
                            print(f"开始分析数据库: {output_path}")
                            
                            try:
                                report_path = generate_analysis_report(output_path, analysis_dir, is_qq)
                                print(f"分析完成! 报告保存到: {report_path}")
                                self.last_report_path = report_path
                            except Exception as e:
                                print(f"分析数据库时出错: {e}")
                else:
                    print(f"解密失败: {db_path}")
            
            # 更新状态
            self.root.after(0, lambda: self.status_var.set(f"解密完成，成功 {success_count}/{len(self.found_databases)} 个数据库"))
            
            if success_count > 0:
                print("\n成功解密的数据库可在以下目录找到:")
                print(f"{os.path.abspath(output_dir)}")
        
        except Exception as e:
            print(f"解密过程出错: {e}")
            self.root.after(0, lambda: self.status_var.set("解密出错"))
        
        finally:
            # 恢复stdout
            sys.stdout = orig_stdout
            self.redirector = None
    
    def clear_decrypt_log(self):
        """清除解密日志"""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")
    
    def start_analysis(self):
        """开始分析选中的数据库文件"""
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            messagebox.showerror("错误", "请选择有效的数据库文件")
            return
        
        is_qq = (self.db_type_var.get() == "QQ")
        
        # 创建分析目录
        analysis_dir = os.path.join(os.path.dirname(db_path), 'analysis')
        
        # 重定向stdout
        orig_stdout = sys.stdout
        self.analysis_redirector = RedirectText(self.analysis_log_text)
        sys.stdout = self.analysis_redirector
        
        threading.Thread(target=self._analysis_thread, args=(db_path, analysis_dir, is_qq, orig_stdout), daemon=True).start()
    
    def _analysis_thread(self, db_path, analysis_dir, is_qq, orig_stdout):
        """数据分析线程"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在分析数据库..."))
            
            print(f"开始分析数据库: {db_path}")
            self.last_report_path = generate_analysis_report(db_path, analysis_dir, is_qq)
            print(f"分析完成，报告已保存到: {self.last_report_path}")
            
            self.root.after(0, lambda: self.status_var.set("分析完成"))
        
        except Exception as e:
            print(f"分析过程出错: {e}")
            self.root.after(0, lambda: self.status_var.set("分析出错"))
        
        finally:
            # 恢复stdout
            sys.stdout = orig_stdout
            self.analysis_redirector = None
    
    def view_report(self):
        """查看分析报告"""
        if not self.last_report_path or not os.path.exists(self.last_report_path):
            messagebox.showinfo("提示", "没有可用的分析报告")
            return
        
        # 使用系统默认浏览器打开HTML报告
        import webbrowser
        webbrowser.open(self.last_report_path)
    
    def clear_analysis_log(self):
        """清除分析日志"""
        self.analysis_log_text.configure(state="normal")
        self.analysis_log_text.delete(1.0, tk.END)
        self.analysis_log_text.configure(state="disabled")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if directory:
            self.output_path_var.set(directory)
    
    def browse_db_file(self):
        """浏览数据库文件"""
        filetypes = (
            ('数据库文件', '*.db'),
            ('所有文件', '*.*')
        )
        filename = filedialog.askopenfilename(
            title='选择数据库文件',
            initialdir=os.getcwd(),
            filetypes=filetypes)
        
        if filename:
            self.db_path_var.set(filename)
            
            # 根据文件名自动推测类型
            if 'qq' in filename.lower() or 'msg3.0' in filename.lower():
                self.db_type_var.set("QQ")
            else:
                self.db_type_var.set("微信")
    
    def get_available_drives(self):
        """获取系统中所有可用的驱动器"""
        drives = []
        if platform.system() == 'Windows':
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:"
                if os.path.exists(drive):
                    drives.append(drive)
        return drives
    
    def show_error(self, message):
        """显示错误消息"""
        messagebox.showerror("错误", message)
    
    def on_close(self):
        """窗口关闭事件"""
        # 关闭重定向
        if hasattr(self, 'text_redirector') and self.text_redirector:
            self.text_redirector.close()
        if hasattr(self, 'analysis_redirector') and self.analysis_redirector:
            self.analysis_redirector.close()
        
        self.root.destroy()

def start_gui():
    """启动GUI应用"""
    root = tk.Tk()
    app = WxDecryptApp(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
