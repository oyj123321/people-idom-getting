#!/usr/bin/env python
"""
修复GUI文件脚本 - 在GUI文件头部添加platform导入
"""
import os

# GUI文件路径
gui_file = os.path.join('wxdecrypt', 'gui.py')

# 检查文件是否存在
if not os.path.exists(gui_file):
    print(f"错误: GUI文件不存在: {gui_file}")
    exit(1)

# 读取文件内容
with open(gui_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已导入platform
if 'import platform' in content:
    print("platform模块已导入，无需修复")
    exit(0)

# 在导入部分添加platform
if 'import time' in content:
    fixed_content = content.replace('import time', 'import time\nimport platform')
    print("找到time导入，在其后添加platform导入")
elif 'from typing' in content:
    fixed_content = content.replace('from typing', 'import platform\nfrom typing')
    print("找到typing导入，在其前添加platform导入")
else:
    # 在文件头部添加
    import_line = '"""\nGUI界面模块，提供图形用户界面操作\n"""\n'
    if import_line in content:
        fixed_content = content.replace(import_line, import_line + 'import platform\n')
        print("在文件头部添加platform导入")
    else:
        # 简单地在文件开头添加
        fixed_content = 'import platform\n' + content
        print("在文件开头添加platform导入")

# 写回文件
with open(gui_file, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print(f"成功修复GUI文件: {gui_file}")
print("现在尝试运行: python run.py") 