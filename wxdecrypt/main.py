"""
微信/QQ数据库自动识别与解密工具主程序
"""
import os
import sys
import argparse
from typing import List, Dict, Any

from wxdecrypt.wechat_path import get_wechat_db_path
from wxdecrypt.db_decrypt import WeChatDBDecrypt
from wxdecrypt import __version__

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='微信/QQ数据库自动识别与解密工具')
    parser.add_argument('-o', '--output', default='./output', 
                       help='解密后数据库保存路径 (默认: ./output)')
    parser.add_argument('-v', '--version', action='store_true',
                       help='显示版本信息')
    parser.add_argument('-l', '--list', action='store_true',
                       help='仅列出找到的数据库，不执行解密')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='静默模式，减少输出信息')
    parser.add_argument('-t', '--test', action='store_true',
                       help='测试模式，不需要真实的微信程序，使用模拟数据')
    
    # 暂不支持的选项，预留
    parser.add_argument('--qq', action='store_true', 
                       help='处理QQ数据库 (暂不支持)')
    
    return parser.parse_args()

def list_databases():
    """列出所有找到的数据库"""
    print("正在查找微信数据库...")
    db_paths = get_wechat_db_path()
    
    if not db_paths:
        print("\n未找到任何微信数据库")
        print("\n可能的原因：")
        print("1. 微信未安装或未登录")
        print("2. 微信安装在非标准位置")
        print("3. 您的系统可能使用了非标准路径")
        print("\n建议操作：")
        print("1. 确保微信已安装并成功登录")
        print("2. 手动指定微信数据库路径（功能开发中）")
        return
    
    print(f"\n找到 {len(db_paths)} 个微信数据库:")
    for idx, db in enumerate(db_paths, 1):
        print(f"{idx}. 用户名: {db['username']}")
        print(f"   微信ID: {db['wxid']}")
        print(f"   数据库: {db['db_name']}")
        print(f"   路径: {db['path']}")
        print()

def decrypt_databases(output_dir: str, quiet: bool = False, test_mode: bool = False):
    """解密所有找到的数据库"""
    if not quiet:
        print("开始自动查找并解密微信数据库...")
    
    decryptor = WeChatDBDecrypt()
    if test_mode:
        decryptor.test_mode = True
        
    results = decryptor.auto_find_and_decrypt(output_dir)
    
    if not results:
        print("未能解密任何数据库")
        if not test_mode:
            print("\n可能的原因：")
            print("1. 未找到微信数据库")
            print("2. 微信未登录或密钥获取失败")
            print("3. 系统权限不足")
            print("\n建议操作：")
            print("1. 确保微信已登录")
            print("2. 以管理员权限运行本程序")
            print("3. 尝试使用测试模式: wxdecrypt -t")
        return
    
    success_count = sum(1 for r in results if r['success'])
    if not quiet:
        print(f"\n成功解密 {success_count} 个数据库:")
        for result in results:
            if result['success']:
                print(f"用户: {result['original']['username']}")
                print(f"数据库: {result['original']['db_name']}")
                print(f"解密路径: {result['decrypted_path']}")
                print("-" * 50)
        
        if success_count > 0:
            print("\n您现在可以:")
            print("1. 使用SQLite浏览器查看解密后的数据库")
            print("2. 使用数据库导出功能将聊天记录导出为其他格式（功能开发中）")
    else:
        print(f"成功解密 {success_count} 个数据库")

def test_program():
    """测试程序基本功能"""
    print("正在测试程序基本功能...")
    print("此模式使用模拟数据，不需要真实的微信程序")
    
    # 创建测试数据
    test_dir = os.path.join(os.getcwd(), "test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建测试数据库文件
    test_db_path = os.path.join(test_dir, "test.db")
    with open(test_db_path, "wb") as f:
        # 写入简单的SQLite头部
        f.write(b"SQLite format 3\0")
        # 填充一些随机数据
        f.write(os.urandom(1024))
    
    print(f"创建测试数据库: {test_db_path}")
    
    # 创建输出目录
    output_dir = os.path.join(os.getcwd(), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"输出目录: {output_dir}")
    print("测试结束")
    
    return output_dir

def main():
    """主函数"""
    print(f"微信/QQ数据库自动识别与解密工具 v{__version__}")
    print("=" * 60)
    
    args = parse_args()
    
    if args.version:
        return
    
    if args.qq:
        print("QQ数据库处理功能暂未实现")
        return
    
    if args.test:
        output_dir = test_program()
        decrypt_databases(output_dir, args.quiet, True)
        return
    
    if args.list:
        list_databases()
        return
    
    decrypt_databases(args.output, args.quiet)

if __name__ == "__main__":
    main() 