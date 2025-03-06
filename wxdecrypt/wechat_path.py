"""
微信数据库路径查找工具
支持自动识别微信数据库路径
"""
import os
import re
import winreg
import time
from typing import List, Dict, Optional, Tuple, Union
import platform
import string

def get_wechat_db_path(search_drives: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    自动识别微信数据库路径
    
    Args:
        search_drives: 指定要搜索的驱动器列表，如['C:', 'D:']。默认为None（自动检测所有驱动器）
    
    Returns:
        List[Dict[str, str]]: 包含微信数据库路径信息的列表，每个项目为一个用户的数据
            {
                'username': 微信用户名,
                'wxid': 微信ID,
                'path': 数据库路径,
            }
    """
    found_dbs = []
    
    # 检查操作系统类型
    system = platform.system()
    if system != 'Windows':
        print(f"当前只支持Windows系统，您的系统是{system}")
        return found_dbs
    
    # 1. 首先尝试快速查找方法（基于已知路径）
    found_dbs = find_wechat_db_by_known_paths()
    
    # 2. 如果没有找到，尝试系统级全局搜索
    if not found_dbs:
        print("未在默认位置找到微信数据库，将进行系统搜索（可能需要较长时间）...")
        found_dbs = find_wechat_db_by_global_search(search_drives)
    
    return found_dbs

def find_wechat_db_by_known_paths() -> List[Dict[str, str]]:
    """基于已知路径模式快速查找微信数据库"""
    found_dbs = []
    
    # 尝试多个可能的路径
    possible_paths = []
    
    # 1. 从注册表获取路径
    registry_path = get_wechat_path_from_registry()
    if registry_path:
        possible_paths.append(registry_path)
    
    # 2. 默认路径
    user_profile = os.environ.get('USERPROFILE', '')
    default_paths = [
        os.path.join(user_profile, 'Documents', 'WeChat Files'),
        os.path.join(user_profile, 'Documents', 'Tencent Files'),
        os.path.join(user_profile, 'Documents', 'My Documents', 'WeChat Files'),
        os.path.join(user_profile, 'WeChat Files'),
        os.path.join("C:\\", "Program Files (x86)", "Tencent", "WeChat", "WeChat Files"),
        os.path.join(user_profile, 'AppData', 'Roaming', 'Tencent', 'WeChat'),
        os.path.join(user_profile, 'AppData', 'Roaming', 'Tencent', 'MicroMsg')
    ]
    
    possible_paths.extend(default_paths)
    
    # 去重并筛选存在的路径
    unique_paths = []
    for path in possible_paths:
        if path and os.path.exists(path) and path not in unique_paths:
            unique_paths.append(path)
    
    if not unique_paths:
        return found_dbs
        
    # 从所有可能的路径中查找数据库
    for wechat_files_path in unique_paths:
        print(f"检查路径: {wechat_files_path}")
        
        # 获取所有用户文件夹
        try:
            wechat_user_folders = [
                folder for folder in os.listdir(wechat_files_path)
                if os.path.isdir(os.path.join(wechat_files_path, folder)) and folder != 'All Users' and folder != 'Applet'
            ]
        except Exception as e:
            print(f"无法读取目录 {wechat_files_path}: {e}")
            continue
        
        # 查找每个用户的数据库
        for user_folder in wechat_user_folders:
            user_path = os.path.join(wechat_files_path, user_folder)
            
            # 可能的数据库目录
            possible_db_dirs = [
                os.path.join(user_path, 'Msg'),
                os.path.join(user_path, 'MsgDB'),
                os.path.join(user_path, 'Db'),
                os.path.join(user_path, 'MicroMsg'),  # 特别关注的路径，包含EnMicroMsg.db
                user_path
            ]
            
            for db_dir in possible_db_dirs:
                if not os.path.exists(db_dir):
                    continue
                
                # 查找数据库文件
                for root, dirs, files in os.walk(db_dir):
                    for file in files:
                        # 特别关注 EnMicroMsg.db，这是微信主要的聊天记录数据库
                        if file == 'EnMicroMsg.db' or file.endswith('.db'):
                            db_path = os.path.join(root, file)
                            
                            # 如果是EnMicroMsg.db，标记为主要数据库
                            is_main_db = (file == 'EnMicroMsg.db')
                            
                            found_dbs.append({
                                'username': user_folder,
                                'wxid': _extract_wxid_from_path(user_folder),
                                'path': db_path,
                                'db_name': file,
                                'is_main_db': is_main_db
                            })
    
    return found_dbs

def find_wechat_db_by_global_search(search_drives: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    通过全局搜索查找微信数据库文件
    
    Args:
        search_drives: 要搜索的驱动器列表，如果为None则搜索所有可用驱动器
    
    Returns:
        List[Dict[str, str]]: 找到的数据库信息列表
    """
    found_dbs = []
    
    # 如果未指定驱动器，获取所有可用驱动器
    if not search_drives:
        search_drives = get_available_drives()
        print(f"将在这些驱动器中搜索: {', '.join(search_drives)}")
    
    # 在每个驱动器中搜索
    target_files = ['EnMicroMsg.db']  # 重点查找的文件
    
    # 排除目录列表，这些目录会跳过搜索以提高效率
    exclude_dirs = [
        'Windows', 'Program Files', 'Program Files (x86)',
        '$Recycle.Bin', 'System Volume Information',
    ]
    
    # 搜索每个驱动器
    for drive in search_drives:
        print(f"\n开始搜索驱动器 {drive}，寻找微信数据库...")
        
        for root, dirs, files in os.walk(drive):
            # 排除系统目录和临时文件夹
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # 如果路径中包含某些关键词，优先处理，这可以加速找到数据库的速度
            path_priority = 0
            if 'Tencent' in root or 'WeChat' in root or 'MicroMsg' in root:
                path_priority = 1
                
            # 检查文件
            for file in files:
                if file in target_files or (file.endswith('.db') and 'wx' in root.lower()):
                    # 找到可能的微信数据库
                    db_path = os.path.join(root, file)
                    
                    # 尝试提取用户信息
                    username = os.path.basename(os.path.dirname(root)) if 'MicroMsg' in root else 'unknown'
                    wxid = _extract_wxid_from_path(root)
                    
                    # 优先级：EnMicroMsg.db > 其他.db文件
                    is_main_db = (file == 'EnMicroMsg.db')
                    
                    found_dbs.append({
                        'username': username,
                        'wxid': wxid,
                        'path': db_path,
                        'db_name': file,
                        'is_main_db': is_main_db,
                        'priority': path_priority  # 路径优先级
                    })
                    
                    # 打印找到的文件
                    print(f"找到可能的微信数据库: {db_path}")
                    
                    # 如果找到EnMicroMsg.db，尝试提取更多相关文件
                    if is_main_db:
                        parent_dir = os.path.dirname(db_path)
                        # 查找同目录下的其他数据库文件
                        for other_file in os.listdir(parent_dir):
                            if other_file != file and other_file.endswith('.db'):
                                other_path = os.path.join(parent_dir, other_file)
                                found_dbs.append({
                                    'username': username,
                                    'wxid': wxid,
                                    'path': other_path,
                                    'db_name': other_file,
                                    'is_main_db': False,
                                    'priority': path_priority
                                })
                                print(f"找到相关数据库: {other_path}")
    
    # 按优先级排序结果
    found_dbs.sort(key=lambda x: (-x.get('priority', 0), -x.get('is_main_db', False)))
    
    return found_dbs

def get_qq_db_path(search_drives: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    自动识别QQ数据库路径
    
    Args:
        search_drives: 指定要搜索的驱动器列表，如['C:', 'D:']。默认为None（自动检测所有驱动器）
    
    Returns:
        List[Dict[str, str]]: 包含QQ数据库路径信息的列表
    """
    found_dbs = []
    
    # 检查操作系统类型
    system = platform.system()
    if system != 'Windows':
        print(f"当前只支持Windows系统，您的系统是{system}")
        return found_dbs
    
    # 1. 首先尝试快速查找方法
    found_dbs = find_qq_db_by_known_paths()
    
    # 2. 如果没有找到，尝试系统级全局搜索
    if not found_dbs:
        print("未在默认位置找到QQ数据库，将进行系统搜索（可能需要较长时间）...")
        found_dbs = find_qq_db_by_global_search(search_drives)
    
    return found_dbs

def find_qq_db_by_known_paths() -> List[Dict[str, str]]:
    """基于已知路径模式快速查找QQ数据库"""
    found_dbs = []
    
    # QQ可能的数据文件夹路径
    user_profile = os.environ.get('USERPROFILE', '')
    qq_paths = [
        os.path.join(user_profile, 'Documents', 'Tencent Files'),
        os.path.join(user_profile, 'AppData', 'Roaming', 'Tencent', 'QQ'),
        os.path.join(user_profile, 'AppData', 'Roaming', 'Tencent', 'QQMiniDL'),
        os.path.join(user_profile, 'Documents', 'My Documents', 'Tencent Files')
    ]
    
    # 尝试从注册表获取QQ路径
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\QQ")
        install_path = winreg.QueryValueEx(key, "Path")[0]
        if install_path and os.path.exists(install_path):
            qq_paths.append(install_path)
        winreg.CloseKey(key)
    except Exception:
        pass
    
    # 查找所有可能的QQ数据库文件
    for qq_path in qq_paths:
        if not os.path.exists(qq_path):
            continue
            
        print(f"检查QQ路径: {qq_path}")
        
        # 递归查找所有Msg*.db文件
        for root, dirs, files in os.walk(qq_path):
            for file in files:
                # QQ消息数据库通常是Msg*.db，特别是Msg3.0.db
                if file.startswith('Msg') and file.endswith('.db'):
                    db_path = os.path.join(root, file)
                    
                    # 尝试从路径提取QQ号
                    qqid = _extract_qqid_from_path(root)
                    
                    found_dbs.append({
                        'qqid': qqid,
                        'path': db_path,
                        'db_name': file
                    })
    
    return found_dbs

def find_qq_db_by_global_search(search_drives: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    通过全局搜索查找QQ数据库文件
    
    Args:
        search_drives: 要搜索的驱动器列表，如果为None则搜索所有可用驱动器
    
    Returns:
        List[Dict[str, str]]: 找到的数据库信息列表
    """
    found_dbs = []
    
    # 如果未指定驱动器，获取所有可用驱动器
    if not search_drives:
        search_drives = get_available_drives()
        print(f"将在这些驱动器中搜索: {', '.join(search_drives)}")
    
    # 在每个驱动器中搜索
    target_files = ['Msg3.0.db']  # 重点查找的文件
    
    # 排除目录列表，这些目录会跳过搜索以提高效率
    exclude_dirs = [
        'Windows', 'Program Files', 'Program Files (x86)',
        '$Recycle.Bin', 'System Volume Information',
    ]
    
    # 搜索每个驱动器
    for drive in search_drives:
        print(f"\n开始搜索驱动器 {drive}，寻找QQ数据库...")
        
        for root, dirs, files in os.walk(drive):
            # 排除系统目录和临时文件夹
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # 如果路径中包含某些关键词，优先处理
            path_priority = 0
            if 'Tencent' in root or 'QQ' in root:
                path_priority = 1
                
            # 检查文件
            for file in files:
                if file in target_files or (file.startswith('Msg') and file.endswith('.db')):
                    # 找到可能的QQ数据库
                    db_path = os.path.join(root, file)
                    
                    # 尝试提取QQ号
                    qqid = _extract_qqid_from_path(root)
                    
                    found_dbs.append({
                        'qqid': qqid,
                        'path': db_path,
                        'db_name': file,
                        'priority': path_priority  # 路径优先级
                    })
                    
                    # 打印找到的文件
                    print(f"找到可能的QQ数据库: {db_path}")
    
    # 按优先级排序结果
    found_dbs.sort(key=lambda x: -x.get('priority', 0))
    
    return found_dbs

def get_wechat_path_from_registry() -> Optional[str]:
    """
    从注册表获取微信文件路径
    
    Returns:
        Optional[str]: 微信文件路径，如果未找到则返回None
    """
    try:
        # 尝试多个可能的注册表路径
        possible_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat"),
            (winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChatApp"),
            (winreg.HKEY_CURRENT_USER, r"Software\Tencent\WXWork"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Tencent\WeChat")
        ]
        
        for hkey, key_path in possible_keys:
            try:
                key = winreg.OpenKey(hkey, key_path)
                try:
                    # 尝试不同的值名
                    for value_name in ["FileSavePath", "InstallPath"]:
                        try:
                            install_path = winreg.QueryValueEx(key, value_name)[0]
                            if install_path == "MyDocument:":
                                # 默认位置，使用系统文档目录
                                user_profile = os.environ.get('USERPROFILE', '')
                                return os.path.join(user_profile, 'Documents', 'WeChat Files')
                            else:
                                # 自定义位置
                                if "WeChat Files" not in install_path:
                                    install_path = os.path.join(install_path, 'WeChat Files')
                                return install_path
                        except:
                            continue
                finally:
                    winreg.CloseKey(key)
            except:
                continue
                
    except Exception as e:
        print(f"读取注册表时出错: {e}")
    
    return None

def get_available_drives() -> List[str]:
    """
    获取系统中所有可用的驱动器
    
    Returns:
        List[str]: 驱动器列表，如['C:', 'D:']
    """
    if platform.system() == 'Windows':
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:"
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    else:
        return ['/']  # 在非Windows系统上，返回根目录

def _extract_wxid_from_path(path: str) -> str:
    """从路径中提取微信ID
    
    Args:
        path: 文件路径字符串
    
    Returns:
        str: 提取出的wxid，如果没有，则返回原路径
    """
    # 尝试匹配wxid_开头的ID
    match = re.search(r'wxid_\w+', path)
    if match:
        return match.group(0)
    return path

def _extract_qqid_from_path(path: str) -> str:
    """从路径中提取QQ号
    
    Args:
        path: 文件路径字符串
    
    Returns:
        str: 提取出的QQ号，如果没有，则返回unknown
    """
    # QQ号通常是纯数字
    match = re.search(r'[1-9]\d{4,11}', path)
    if match:
        return match.group(0)
    return "unknown"

if __name__ == "__main__":
    # 测试微信数据库查找功能
    print("查找微信数据库...")
    start_time = time.time()
    db_paths = get_wechat_db_path()
    elapsed = time.time() - start_time
    
    print(f"查找完成，耗时: {elapsed:.2f}秒")
    print(f"找到 {len(db_paths)} 个微信数据库:")
    for db in db_paths:
        print(f"用户: {db['username']}")
        print(f"微信ID: {db['wxid']}")
        print(f"是否主数据库: {'是' if db.get('is_main_db', False) else '否'}")
        print(f"数据库: {db['db_name']}")
        print(f"路径: {db['path']}")
        print("-" * 50)
    
    # 测试QQ数据库查找功能
    print("\n查找QQ数据库...")
    start_time = time.time()
    qq_dbs = get_qq_db_path()
    elapsed = time.time() - start_time
    
    print(f"查找完成，耗时: {elapsed:.2f}秒")
    print(f"找到 {len(qq_dbs)} 个QQ数据库:")
    for db in qq_dbs:
        print(f"QQ号: {db['qqid']}")
        print(f"数据库: {db['db_name']}")
        print(f"路径: {db['path']}")
        print("-" * 50) 