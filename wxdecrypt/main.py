"""
微信/QQ数据库自动识别与解密工具主程序
"""
import os
import sys
import argparse
from typing import List, Dict, Any

from wxdecrypt.wechat_path import get_wechat_db_path, get_qq_db_path
from wxdecrypt.db_decrypt import WeChatDBDecrypt
from wxdecrypt import __version__

# 导入数据分析模块（如果安装了相关依赖）
try:
    from wxdecrypt.data_analysis import generate_analysis_report
    HAS_ANALYSIS = True
except ImportError:
    HAS_ANALYSIS = False

# 尝试导入GUI模块
try:
    from wxdecrypt.gui import start_gui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

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
    
    # 指定搜索驱动器
    parser.add_argument('-d', '--drives', 
                       help='指定要搜索的驱动器，用逗号分隔，如"C:,D:",如果不指定则自动搜索所有驱动器')
    parser.add_argument('-f', '--full-scan', action='store_true',
                       help='进行全盘搜索，可能需要较长时间')
    
    # QQ相关选项
    parser.add_argument('--qq', action='store_true', 
                       help='处理QQ数据库')
    parser.add_argument('--both', action='store_true',
                       help='同时处理微信和QQ数据库')
    
    # 数据分析选项
    if HAS_ANALYSIS:
        parser.add_argument('-a', '--analyze', action='store_true',
                          help='解密后进行数据分析，生成可视化图表和词频分析')
        parser.add_argument('--analyze-only', 
                          help='仅对指定的已解密数据库文件进行分析，不执行解密操作')
    
    # GUI选项
    parser.add_argument('--cli', action='store_true',
                       help='使用命令行界面而不是图形界面')
    
    return parser.parse_args()

def list_databases(list_qq=False, drives=None, full_scan=False):
    """列出所有找到的数据库"""
    # 处理驱动器参数
    search_drives = parse_drives(drives) if drives else None
    
    if not list_qq:
        print("正在查找微信数据库...")
        db_paths = get_wechat_db_path(search_drives) if full_scan or drives else get_wechat_db_path()
        
        if not db_paths:
            print("\n未找到任何微信数据库")
            print("\n可能的原因：")
            print("1. 微信未安装或未登录")
            print("2. 微信安装在非标准位置")
            print("3. 您的系统可能使用了非标准路径")
            print("\n建议操作：")
            print("1. 确保微信已安装并成功登录")
            print("2. 尝试使用全盘搜索: wxdecrypt -l -f")
            print("3. 尝试指定特定驱动器搜索: wxdecrypt -l -d D:,E:")
            print("4. 尝试运行带--qq参数查找QQ数据库: wxdecrypt -l --qq")
            return
        
        print(f"\n找到 {len(db_paths)} 个微信数据库:")
        for idx, db in enumerate(db_paths, 1):
            print(f"{idx}. 用户名: {db['username']}")
            print(f"   微信ID: {db['wxid']}")
            print(f"   数据库: {db['db_name']}")
            print(f"   是否主数据库: {'是' if db.get('is_main_db', False) else '否'}")
            print(f"   路径: {db['path']}")
            print()
    else:
        print("正在查找QQ数据库...")
        qq_dbs = get_qq_db_path(search_drives) if full_scan or drives else get_qq_db_path()
        
        if not qq_dbs:
            print("\n未找到任何QQ数据库")
            print("\n可能的原因：")
            print("1. QQ未安装或未登录")
            print("2. QQ安装在非标准位置")
            print("\n建议操作：")
            print("1. 确保QQ已安装并成功登录")
            print("2. 尝试使用全盘搜索: wxdecrypt -l --qq -f")
            print("3. 尝试指定特定驱动器搜索: wxdecrypt -l --qq -d D:,E:")
            return
        
        print(f"\n找到 {len(qq_dbs)} 个QQ数据库:")
        for idx, db in enumerate(qq_dbs, 1):
            print(f"{idx}. QQ号: {db['qqid']}")
            print(f"   数据库: {db['db_name']}")
            print(f"   路径: {db['path']}")
            print()

def decrypt_databases(output_dir: str, quiet: bool = False, test_mode: bool = False, decrypt_qq: bool = False, drives=None, full_scan=False, analyze=False):
    """解密所有找到的数据库"""
    # 处理驱动器参数
    search_drives = parse_drives(drives) if drives else None
    
    if not quiet:
        if not decrypt_qq:
            print("开始自动查找并解密微信数据库...")
        else:
            print("开始自动查找并解密QQ数据库...")
    
    decryptor = WeChatDBDecrypt()
    if test_mode:
        decryptor.test_mode = True
    
    if decrypt_qq:
        decryptor.decrypt_qq = True
    
    # 设置搜索驱动器
    decryptor.search_drives = search_drives
    decryptor.full_scan = full_scan
        
    results = decryptor.auto_find_and_decrypt(output_dir)
    
    if not results:
        print("未能解密任何数据库")
        if not test_mode:
            print("\n可能的原因：")
            print("1. 未找到数据库")
            print("2. 应用未登录或密钥获取失败")
            print("3. 系统权限不足")
            print("\n建议操作：")
            print("1. 确保应用已登录")
            print("2. 尝试指定搜索驱动器: wxdecrypt -d D:,E:")
            print("3. 尝试全盘搜索: wxdecrypt -f")
            print("4. 以管理员权限运行本程序")
            print("5. 尝试使用测试模式: wxdecrypt -t")
        return
    
    success_count = sum(1 for r in results if r['success'])
    if not quiet:
        print(f"\n成功解密 {success_count} 个数据库:")
        for result in results:
            if result['success']:
                if 'username' in result['original']:
                    # 微信数据库
                    print(f"用户: {result['original']['username']}")
                    print(f"微信ID: {result['original'].get('wxid', 'unknown')}")
                else:
                    # QQ数据库
                    print(f"QQ号: {result['original'].get('qqid', 'unknown')}")
                print(f"数据库: {result['original']['db_name']}")
                print(f"解密路径: {result['decrypted_path']}")
                print("-" * 50)
        
        if success_count > 0:
            print("\n您现在可以:")
            print("1. 使用SQLite浏览器查看解密后的数据库")
            print("2. 使用数据库导出功能将聊天记录导出为其他格式（功能开发中）")
            if HAS_ANALYSIS:
                print("3. 使用 -a 参数对解密后的数据库进行分析")
    else:
        print(f"成功解密 {success_count} 个数据库")
    
    # 如果需要分析并且存在成功解密的数据库，进行数据分析
    if analyze and HAS_ANALYSIS and success_count > 0:
        analyze_decrypted_results(results, decrypt_qq)
    
    return results

def analyze_decrypted_results(results, is_qq=False):
    """分析解密后的数据库"""
    print("\n开始分析解密后的数据库...")
    
    success_results = [r for r in results if r['success']]
    for result in success_results:
        db_path = result['decrypted_path']
        # 为每个数据库创建单独的分析目录
        analysis_dir = os.path.join(os.path.dirname(db_path), 'analysis')
        
        if 'username' in result['original']:
            # 微信数据库
            print(f"\n分析微信数据库: {db_path}")
            name = result['original']['username']
            is_main = result['original'].get('is_main_db', False)
            
            # 仅分析主要数据库或消息相关数据库
            if is_main or 'msg' in result['original']['db_name'].lower():
                try:
                    report_path = generate_analysis_report(db_path, analysis_dir, False)
                    print(f"分析报告已保存到: {report_path}")
                except Exception as e:
                    print(f"分析数据库时出错: {e}")
            else:
                print(f"跳过非消息数据库: {db_path}")
        else:
            # QQ数据库
            print(f"\n分析QQ数据库: {db_path}")
            try:
                report_path = generate_analysis_report(db_path, analysis_dir, True)
                print(f"分析报告已保存到: {report_path}")
            except Exception as e:
                print(f"分析数据库时出错: {e}")

def analyze_single_database(db_path, is_qq=False):
    """分析指定的单个数据库"""
    if not HAS_ANALYSIS:
        print("错误: 数据分析功能不可用，请安装必要的依赖")
        return False
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    # 创建分析目录
    analysis_dir = os.path.join(os.path.dirname(db_path), 'analysis')
    
    try:
        print(f"开始分析数据库: {db_path}")
        report_path = generate_analysis_report(db_path, analysis_dir, is_qq)
        print(f"分析完成! 报告已保存到: {report_path}")
        return True
    except Exception as e:
        print(f"分析数据库时出错: {e}")
        return False

def parse_drives(drives_str: str) -> List[str]:
    """解析驱动器字符串，返回驱动器列表"""
    if not drives_str:
        return None
    
    # 按逗号分隔，去除空格，保留非空项
    drives = [d.strip() for d in drives_str.split(',') if d.strip()]
    
    # 确保每个驱动器都有冒号结尾
    drives = [d if d.endswith(':') else d + ':' for d in drives]
    
    # 验证每个驱动器是否存在
    valid_drives = []
    for drive in drives:
        if os.path.exists(drive):
            valid_drives.append(drive)
        else:
            print(f"警告: 驱动器 {drive} 不存在或无法访问")
    
    return valid_drives if valid_drives else None

def test_program():
    """测试程序基本功能"""
    print("正在测试程序基本功能...")
    print("此模式使用模拟数据，不需要真实的应用程序")
    
    # 创建测试数据
    test_dir = os.path.join(os.getcwd(), "test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建微信测试数据库文件
    test_wx_db_path = os.path.join(test_dir, "EnMicroMsg.db")
    with open(test_wx_db_path, "wb") as f:
        # 写入简单的SQLite头部
        f.write(b"SQLite format 3\0")
        # 填充一些随机数据
        f.write(os.urandom(1024))
    
    # 创建QQ测试数据库文件
    test_qq_db_path = os.path.join(test_dir, "Msg3.0.db")
    with open(test_qq_db_path, "wb") as f:
        # 写入简单的SQLite头部
        f.write(b"SQLite format 3\0")
        # 填充一些随机数据
        f.write(os.urandom(1024))
    
    print(f"创建测试数据库: {test_wx_db_path}")
    print(f"创建测试数据库: {test_qq_db_path}")
    
    # 创建输出目录
    output_dir = os.path.join(os.getcwd(), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"输出目录: {output_dir}")
    print("测试结束")
    
    return output_dir

def check_dependencies():
    """检查是否安装了数据分析所需的依赖"""
    if not HAS_ANALYSIS:
        print("\n提示: 数据分析功能不可用，若要使用请安装以下依赖:")
        print("pip install pandas numpy matplotlib jieba wordcloud")
        print("或使用: pip install -r requirements-analysis.txt")

def run_cli():
    """运行命令行界面"""
    args = parse_args()
    
    if args.version:
        print(f"微信/QQ数据库自动识别与解密工具 v{__version__}")
        return
    
    # 检查依赖
    check_dependencies()
    
    # 如果指定了只分析模式
    if HAS_ANALYSIS and hasattr(args, 'analyze_only') and args.analyze_only:
        db_path = args.analyze_only
        is_qq = args.qq or ('qq' in db_path.lower() or 'msg3.0' in db_path.lower())
        if analyze_single_database(db_path, is_qq):
            print("\n分析完成!")
        return
    
    if args.test:
        output_dir = test_program()
        if args.qq:
            decrypt_databases(output_dir, args.quiet, True, True, None, False, 
                             HAS_ANALYSIS and getattr(args, 'analyze', False))
        elif args.both:
            decrypt_databases(output_dir, args.quiet, True, False, None, False, 
                             HAS_ANALYSIS and getattr(args, 'analyze', False))
            decrypt_databases(output_dir, args.quiet, True, True, None, False, 
                             HAS_ANALYSIS and getattr(args, 'analyze', False))
        else:
            decrypt_databases(output_dir, args.quiet, True, False, None, False, 
                             HAS_ANALYSIS and getattr(args, 'analyze', False))
        return
    
    if args.list:
        if args.qq:
            list_databases(True, args.drives, args.full_scan)
        elif args.both:
            list_databases(False, args.drives, args.full_scan)
            list_databases(True, args.drives, args.full_scan)
        else:
            list_databases(False, args.drives, args.full_scan)
        return
    
    # 分析功能标志
    analyze = HAS_ANALYSIS and getattr(args, 'analyze', False)
    
    if args.qq:
        decrypt_databases(args.output, args.quiet, False, True, args.drives, args.full_scan, analyze)
    elif args.both:
        decrypt_databases(args.output, args.quiet, False, False, args.drives, args.full_scan, analyze)
        decrypt_databases(args.output, args.quiet, False, True, args.drives, args.full_scan, analyze)
    else:
        decrypt_databases(args.output, args.quiet, False, False, args.drives, args.full_scan, analyze)

def main():
    """主函数，默认启动GUI界面，如果指定了命令行参数则使用命令行界面"""
    print(f"微信/QQ数据库自动识别与解密工具 v{__version__}")
    print("=" * 60)
    
    # 检查命令行参数
    args = sys.argv[1:]
    
    # 如果指定了--cli或其他命令行参数，则使用命令行界面
    if '--cli' in args or len(args) > 0:
        run_cli()
        return
    
    # 否则启动GUI界面
    if HAS_GUI:
        try:
            start_gui()
        except Exception as e:
            print(f"启动GUI界面时出错: {e}")
            print("将使用命令行界面...")
            run_cli()
    else:
        print("GUI界面不可用，将使用命令行界面...")
        run_cli()

if __name__ == "__main__":
    main() 