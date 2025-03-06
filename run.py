#!/usr/bin/env python
"""
微信/QQ数据库自动识别与解密工具启动脚本
"""
import sys
import os
import traceback

# 添加当前目录到搜索路径，确保能够导入wxdecrypt模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("启动微信/QQ数据库解密工具...")
    
    # 尝试导入并启动GUI
    try:
        # 导入启动函数
        from wxdecrypt.gui import start_gui
        
        # 检查是否有命令行参数
        if len(sys.argv) > 1:
            # 有命令行参数，使用命令行模式
            from wxdecrypt.main import run_cli
            print("检测到命令行参数，使用命令行模式...")
            run_cli()
        else:
            # 无命令行参数，启动GUI
            print("启动图形界面...")
            start_gui()
            
    except ImportError as e:
        print(f"GUI导入失败 ({e})，将使用命令行界面...")
        from wxdecrypt.main import run_cli
        run_cli()
    
except Exception as e:
    print(f"程序启动失败: {e}")
    print("详细错误信息:")
    traceback.print_exc()
    
    input("按任意键退出...")
    sys.exit(1)

if __name__ == "__main__":
    pass  # 主要代码已在脚本开始时执行 