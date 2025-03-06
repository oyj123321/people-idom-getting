import os
import sys

def check_file_header(path):
    """检查文件头部以确定文件类型"""
    print(f"检查文件: {path}")
    
    if not os.path.exists(path):
        print(f"文件不存在: {path}")
        return
    
    size = os.path.getsize(path)
    print(f"文件大小: {size} 字节")
    
    with open(path, 'rb') as f:
        header = f.read(16)
        hex_header = ' '.join(f'{b:02x}' for b in header)
        print(f"文件头: {hex_header}")
        
        # 检查是否为SQLite数据库
        if header.startswith(b'SQLite format 3'):
            print("是有效的SQLite数据库文件")
        else:
            print("不是标准的SQLite数据库文件")

# 检查几个不同的文件
db_paths = [
    "D:/群智/output/WeChat/283664393/guild_msg.db",
    "D:/群智/output/WeChat/283664393/FileInfo.db",
    "D:/群智/output/WeChat/radium/Databases.db",
    "D:/群智/output/WeChat/xweb/Databases.db"
]

for path in db_paths:
    print("\n" + "="*50)
    check_file_header(path) 