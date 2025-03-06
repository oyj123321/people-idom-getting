import sqlite3
import os
import sys

def test_db(db_path):
    print(f"测试数据库: {db_path}")
    try:
        # 检查文件大小和是否存在
        if not os.path.exists(db_path):
            print(f"文件不存在: {db_path}")
            return False
            
        size = os.path.getsize(db_path)
        print(f"文件大小: {size} 字节")
        
        # 尝试作为SQLite数据库打开
        conn = sqlite3.connect(db_path)
        print("成功打开数据库连接")
        conn.close()
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

# 测试几个不同的数据库文件
db_paths = [
    "D:/群智/output/WeChat/283664393/guild_msg.db",
    "D:/群智/output/WeChat/283664393/FileInfo.db",
    "D:/群智/output/WeChat/radium/Databases.db",
    "D:/群智/output/WeChat/xweb/Databases.db"
]

for db_path in db_paths:
    print("\n" + "="*50)
    test_db(db_path) 