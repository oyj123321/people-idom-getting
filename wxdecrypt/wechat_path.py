"""
微信数据库路径查找工具
支持自动识别微信数据库路径
"""
import os
import re
import winreg
from typing import List, Dict, Optional, Tuple, Union
import platform

def get_wechat_db_path() -> List[Dict[str, str]]:
    """
    自动识别微信数据库路径
    
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
        os.path.join("C:\\", "Program Files (x86)", "Tencent", "WeChat", "WeChat Files")
    ]
    
    possible_paths.extend(default_paths)
    
    # 去重并筛选存在的路径
    unique_paths = []
    for path in possible_paths:
        if path and os.path.exists(path) and path not in unique_paths:
            unique_paths.append(path)
    
    if not unique_paths:
        print("未找到任何可能的微信文件目录")
        return found_dbs
        
    # 从所有可能的路径中查找数据库
    for wechat_files_path in unique_paths:
        print(f"正在检查路径: {wechat_files_path}")
        
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
                user_path
            ]
            
            for db_dir in possible_db_dirs:
                if not os.path.exists(db_dir):
                    continue
                
                # 查找数据库文件
                for root, dirs, files in os.walk(db_dir):
                    for file in files:
                        if file.endswith('.db'):
                            db_path = os.path.join(root, file)
                            found_dbs.append({
                                'username': user_folder,
                                'wxid': _extract_wxid_from_path(user_folder),
                                'path': db_path,
                                'db_name': file
                            })
    
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

if __name__ == "__main__":
    # 测试函数
    db_paths = get_wechat_db_path()
    print(f"找到 {len(db_paths)} 个微信数据库:")
    for db in db_paths:
        print(f"用户: {db['username']}")
        print(f"微信ID: {db['wxid']}")
        print(f"数据库: {db['db_name']}")
        print(f"路径: {db['path']}")
        print("-" * 50) 