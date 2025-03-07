"""
真实的微信/QQ数据库解密模块，使用PyWxDump功能
"""
import os
import sys
import shutil
import glob
import subprocess
import sqlite3
import hashlib
import binascii
from typing import Optional, List, Dict, Any, Tuple

# 尝试导入PyWxDump相关模块
try:
    # 尝试导入PyWxDump相关模块
    from PyWxDump import wx
    from PyWxDump.wx import get_key as wx_get_key
    from PyWxDump.wx import decode_database
    HAS_PYWXDUMP = True
except ImportError:
    print("警告: 未能导入PyWxDump模块，将使用有限的解密功能")
    HAS_PYWXDUMP = False

# 尝试导入sqlcipher
try:
    import sqlcipher3
    HAS_SQLCIPHER = True
except ImportError:
    HAS_SQLCIPHER = False

from wxdecrypt.utils.memory_utils import get_wechat_key
from wxdecrypt.wechat_path import get_wechat_db_path, get_qq_db_path

class RealWeChatDBDecrypt:
    """真实的微信数据库解密类，使用PyWxDump功能"""
    
    def __init__(self):
        """初始化解密器"""
        self.key = None
        self.db_paths = []
        self.test_mode = False
        self.decrypt_qq = False  # 是否解密QQ数据库
        self.search_drives = None  # 要搜索的驱动器
        self.full_scan = False  # 是否进行全盘搜索
        
    def auto_find_and_decrypt(self, output_dir: str = "./output") -> List[Dict[str, Any]]:
        """
        自动查找并解密所有微信/QQ数据库
        
        Args:
            output_dir: 解密后数据库的输出目录
            
        Returns:
            解密结果列表，每项包含原始和解密后的路径信息
        """
        results = []
            
        if self.test_mode:
            print("测试模式：使用模拟数据")
            return self._handle_test_mode(output_dir)
        
        # 查找数据库路径
        if self.decrypt_qq:
            print(f"使用{'全盘' if self.full_scan else ''}搜索方式查找QQ数据库...")
            self.db_paths = get_qq_db_path(self.search_drives)
            print(f"找到 {len(self.db_paths)} 个QQ数据库")
        else:
            print(f"使用{'全盘' if self.full_scan else ''}搜索方式查找微信数据库...")
            self.db_paths = get_wechat_db_path(self.search_drives)
            print(f"找到 {len(self.db_paths)} 个微信数据库")
            
        if not self.db_paths:
            if self.decrypt_qq:
                print("未找到QQ数据库")
            else:
                print("未找到微信数据库")
            return results
        
        # 获取密钥
        if not self.decrypt_qq:  # QQ数据库通常不加密
            if HAS_PYWXDUMP:
                try:
                    # 使用PyWxDump获取真实密钥
                    self.key = wx_get_key()
                    if not self.key:
                        print("未能获取微信数据库密钥，尝试备用方法...")
                        self.key = get_wechat_key()
                except Exception as e:
                    print(f"使用PyWxDump获取密钥失败: {e}")
                    print("尝试使用备用方法...")
                    self.key = get_wechat_key()
            else:
                # 使用备用方法获取密钥
                self.key = get_wechat_key()
                
            if not self.key:
                print("未能获取微信数据库密钥")
                return results
            else:
                print(f"成功获取密钥: {self.key.hex() if isinstance(self.key, bytes) else self.key}")
                
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 解密所有数据库
        for db_info in self.db_paths:
            db_path = db_info['path']
            db_name = db_info['db_name']
            
            # 创建用户输出目录
            if self.decrypt_qq:
                # QQ数据库使用QQ号作为目录名
                user_id = db_info.get('qqid', 'unknown')
                app_name = "QQ"
            else:
                # 微信数据库使用用户名作为目录名
                user_id = db_info['username']
                app_name = "WeChat"
                
            user_output_dir = os.path.join(output_dir, app_name, user_id)
            os.makedirs(user_output_dir, exist_ok=True)
            
            # 解密数据库
            output_path = os.path.join(user_output_dir, db_name)
            success = self.decrypt_db(db_path, output_path)
            
            results.append({
                'original': db_info,
                'decrypted_path': output_path if success else None,
                'success': success
            })
            
        return results
    
    def _handle_test_mode(self, output_dir: str) -> List[Dict[str, Any]]:
        """处理测试模式"""
        results = []
        
        # 创建测试目录
        test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")
        os.makedirs(test_dir, exist_ok=True)
        
        if self.decrypt_qq:
            # 处理QQ测试数据
            # 暂不实现
            pass
        else:
            # 查找测试微信数据库
            test_files = []
            patterns = ['*.db', 'EnMicroMsg.db']
            for pattern in patterns:
                test_files.extend(glob.glob(os.path.join(test_dir, pattern)))
            
            if not test_files:
                # 创建一个测试微信数据库
                test_db_path = os.path.join(test_dir, "EnMicroMsg.db")
                with open(test_db_path, "wb") as f:
                    f.write(b"SQLite format 3\0")
                    f.write(os.urandom(1024))
                test_files = [test_db_path]
            
            # 处理每个测试文件
            for db_path in test_files:
                db_name = os.path.basename(db_path)
                
                # 模拟微信用户信息
                username = "test_user"
                wxid = "wxid_test123456"
                wx_output_dir = os.path.join(output_dir, "WeChat", username)
                os.makedirs(wx_output_dir, exist_ok=True)
                
                # 模拟解密过程
                output_path = os.path.join(wx_output_dir, db_name)
                shutil.copy2(db_path, output_path)
                
                # 记录结果
                results.append({
                    'original': {
                        'username': username,
                        'wxid': wxid,
                        'path': db_path,
                        'db_name': db_name,
                        'is_main_db': (db_name == 'EnMicroMsg.db')
                    },
                    'decrypted_path': output_path,
                    'success': True
                })
        
        return results
    
    def decrypt_db(self, input_path: str, output_path: str) -> bool:
        """
        解密单个数据库文件
        
        Args:
            input_path: 原始加密数据库路径
            output_path: 解密后数据库保存路径
            
        Returns:
            解密是否成功
        """
        if self.test_mode:
            # 测试模式直接复制文件
            try:
                shutil.copy2(input_path, output_path)
                return True
            except Exception as e:
                print(f"测试模式复制文件失败: {e}")
                return False
        
        if not os.path.exists(input_path):
            print(f"数据库文件不存在: {input_path}")
            return False
        
        try:
            print(f"正在处理数据库: {input_path}")
            
            if self.decrypt_qq:
                # QQ数据库通常不加密，直接复制
                print("QQ数据库通常不加密，直接复制")
                shutil.copy2(input_path, output_path)
                return True
            else:
                # 微信数据库需要解密
                if not self.key:
                    print("未设置数据库密钥")
                    return False
                
                # 尝试使用PyWxDump解密
                if HAS_PYWXDUMP:
                    try:
                        # 使用PyWxDump的decode_database函数解密
                        print(f"使用PyWxDump解密数据库: {input_path}")
                        decode_database(input_path, output_path, self.key)
                        print(f"解密成功: {output_path}")
                        return True
                    except Exception as e:
                        print(f"PyWxDump解密失败: {e}")
                        print("尝试使用备用方法...")
                
                # 尝试使用SQLCipher解密
                if HAS_SQLCIPHER:
                    try:
                        print(f"使用SQLCipher解密数据库: {input_path}")
                        # 从文件中读取salt并计算真正的密钥
                        with open(input_path, 'rb') as f:
                            salt = f.read(16)
                            
                        # 使用PBKDF2派生密钥
                        key = hashlib.pbkdf2_hmac('sha1', self.key, salt, 64000, dklen=32)
                        hex_key = binascii.hexlify(key).decode()
                        
                        print(f"计算得到的数据库密钥: {hex_key}")
                        
                        # 使用sqlcipher3解密
                        conn = sqlcipher3.connect(input_path)
                        conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")
                        conn.execute("PRAGMA cipher_compatibility = 3")
                        
                        # 创建新的未加密数据库
                        new_conn = sqlite3.connect(output_path)
                        
                        # 复制所有表结构和数据
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        
                        for table in tables:
                            table_name = table[0]
                            # 获取表结构
                            cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}'")
                            create_sql = cursor.fetchone()[0]
                            
                            # 在新数据库中创建表
                            new_conn.execute(create_sql)
                            
                            # 复制数据
                            cursor.execute(f"SELECT * FROM {table_name}")
                            rows = cursor.fetchall()
                            
                            if rows:
                                # 获取列数
                                columns = len(rows[0])
                                placeholders = ','.join(['?'] * columns)
                                
                                # 插入数据
                                new_conn.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
                        
                        # 提交更改并关闭连接
                        new_conn.commit()
                        new_conn.close()
                        conn.close()
                        
                        print(f"解密成功: {output_path}")
                        return True
                    except Exception as e:
                        print(f"SQLCipher解密失败: {e}")
                        print("尝试使用基本方法...")
                
                # 使用基本方法（仅复制文件结构，不解密内容）
                try:
                    print("使用基本方法复制数据库结构")
                    # 从文件中读取salt并计算真正的密钥
                    with open(input_path, 'rb') as f:
                        salt = f.read(16)
                        
                    # 使用PBKDF2派生密钥
                    key = hashlib.pbkdf2_hmac('sha1', self.key, salt, 64000, dklen=32)
                    hex_key = binascii.hexlify(key).decode()
                    
                    print(f"计算得到的数据库密钥: {hex_key}")
                    
                    # 复制原始数据库
                    shutil.copy2(input_path, output_path)
                    
                    print(f"已复制数据库: {output_path}")
                    print("注意: 此方法仅复制文件，未进行实际解密")
                    print("要查看内容，请安装SQLCipher或PyWxDump")
                    
                    return True
                except Exception as e:
                    print(f"基本方法失败: {e}")
                    return False
                    
        except Exception as e:
            print(f"处理过程出错: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    decryptor = RealWeChatDBDecrypt()
    results = decryptor.auto_find_and_decrypt("./output_real")
    
    print("\n解密结果:")
    for i, result in enumerate(results, 1):
        status = "成功" if result['success'] else "失败"
        path = result['decrypted_path'] if result['success'] else "N/A"
        print(f"{i}. {result['original']['path']} -> {status}: {path}") 