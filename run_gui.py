#!/usr/bin/env python
"""
微信/QQ数据库解密工具GUI启动脚本
"""
import sys
import os
import traceback

# 添加当前目录到搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入并启动GUI
try:
    print("正在启动GUI界面...")
    
    # 导入并检查tkinter
    try:
        import tkinter
        print("tkinter已安装")
    except ImportError:
        print("错误: tkinter未安装，GUI界面无法启动")
        print("请安装tkinter: 在Windows通常预装，Linux可能需要 'sudo apt-get install python3-tk'")
        sys.exit(1)
    
    # 导入GUI启动函数
    try:
        from wxdecrypt.gui import start_gui
        print("成功导入GUI模块")
    except ImportError as e:
        print(f"错误: 无法导入GUI模块 - {e}")
        print("请确保项目已正确安装")
        sys.exit(1)
    
    # 启动GUI
    print("启动GUI界面...")
    start_gui()
    
except Exception as e:
    print(f"启动GUI时出错: {e}")
    print("错误详情:")
    traceback.print_exc()
    
    # 尝试以命令行方式启动
    print("\n尝试以命令行方式启动...")
    try:
        from wxdecrypt.main import run_cli
        run_cli()
    except Exception as e2:
        print(f"命令行方式启动也失败: {e2}")
        print("请检查项目安装是否正确")
        
if __name__ == "__main__":
    pass  # 主要代码已在脚本开始时执行 