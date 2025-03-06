from wxdecrypt.data_analysis import generate_analysis_report
import os
import sys
import glob

# 查找所有已解密的数据库文件
base_dir = "D:/群智/output/WeChat"
db_files = []

# 递归搜索所有.db文件
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.db'):
            db_path = os.path.join(root, file)
            db_files.append(db_path)

print(f"找到 {len(db_files)} 个数据库文件")

# 尝试分析每个文件
for db_path in db_files:
    print(f"\n尝试分析: {db_path}")
    analysis_dir = os.path.join(os.path.dirname(db_path), 'analysis')
    os.makedirs(analysis_dir, exist_ok=True)
    
    try:
        print(f"开始分析数据库: {db_path}")
        report_path = generate_analysis_report(db_path, analysis_dir, False)
        print(f"分析完成! 报告已保存到: {report_path}")
        # 如果成功分析，退出循环
        print("发现可分析的数据库，停止尝试其他数据库")
        break
    except Exception as e:
        print(f"分析数据库时出错: {e}") 