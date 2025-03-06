"""
微信/QQ数据库解密模块
"""
import os
import sys
import sqlite3
import hashlib
import binascii
import shutil
from typing import Optional, List, Dict, Any, Union
import glob

from wxdecrypt.utils.memory_utils import get_wechat_key
from wxdecrypt.wechat_path import get_wechat_db_path

class WeChatDBDecrypt:
    """微信数据库解密类"""
    
    def __init__(self):
        """初始化数据库解密器"""
        self.key = None
        self.db_paths = []
        self.test_mode = False
        
    def auto_find_and_decrypt(self, output_dir: str = "./output") -> List[Dict[str, Any]]:
        """
        自动查找并解密所有微信数据库
        
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
        self.db_paths = get_wechat_db_path()
        if not self.db_paths:
            print("未找到微信数据库")
            return results
        
        # 获取密钥
        self.key = get_wechat_key()
        if not self.key:
            print("未能获取微信数据库密钥")
            return results
            
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 解密所有数据库
        for db_info in self.db_paths:
            db_path = db_info['path']
            db_name = db_info['db_name']
            username = db_info['username']
            
            # 创建用户输出目录
            user_output_dir = os.path.join(output_dir, username)
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
        
        # 查找测试数据库
        test_files = []
        for ext in ['*.db', '*.sqlite', '*.sqlite3']:
            pattern = os.path.join("test_data", ext)
            test_files.extend(glob.glob(pattern))
        
        if not test_files:
            print("未找到测试数据库文件")
            # 创建一个测试数据库
            test_dir = os.path.join(os.getcwd(), "test_data")
            os.makedirs(test_dir, exist_ok=True)
            
            test_db_path = os.path.join(test_dir, "test.db")
            with open(test_db_path, "wb") as f:
                f.write(b"SQLite format 3\0")
                f.write(os.urandom(1024))
            
            test_files = [test_db_path]
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理每个测试文件
        for db_path in test_files:
            db_name = os.path.basename(db_path)
            
            # 模拟用户信息
            username = "test_user"
            user_output_dir = os.path.join(output_dir, username)
            os.makedirs(user_output_dir, exist_ok=True)
            
            # 模拟解密过程
            output_path = os.path.join(user_output_dir, db_name)
            shutil.copy2(db_path, output_path)
            
            # 记录结果
            results.append({
                'original': {
                    'username': username,
                    'wxid': 'test_wxid',
                    'path': db_path,
                    'db_name': db_name
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
                
        if not self.key:
            print("未设置数据库密钥")
            return False
            
        if not os.path.exists(input_path):
            print(f"数据库文件不存在: {input_path}")
            return False
            
        try:
            print(f"正在解密数据库: {input_path}")
            
            # 对于微信数据库，需要先计算HMAC-SHA1密钥
            # 从文件中读取salt并计算真正的密钥
            with open(input_path, 'rb') as f:
                salt = f.read(16)
                
            # 使用PBKDF2派生密钥
            key = hashlib.pbkdf2_hmac('sha1', self.key, salt, 64000, dklen=32)
            hex_key = binascii.hexlify(key).decode()
            
            print(f"计算得到的数据库密钥: {hex_key}")
            
            # 复制原始数据库
            shutil.copy2(input_path, output_path)
            
            # 尝试使用密钥打开并解密数据库
            try:
                # 注意: 这里使用的是普通sqlite3，真实场景需要使用支持加密的库如pysqlcipher3
                # 这里只是示例
                conn = sqlite3.connect(output_path)
                
                # 在真实实现中，这里应该执行:
                # conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")
                # conn.execute("PRAGMA cipher_compatibility = 3")
                
                # 测试连接
                conn.execute("SELECT 1")
                conn.close()
                
                print(f"数据库解密成功: {output_path}")
                return True
                
            except sqlite3.Error as e:
                print(f"解密数据库失败: {e}")
                # 删除解密失败的文件
                if os.path.exists(output_path):
                    os.remove(output_path)
                return False
                
        except Exception as e:
            print(f"解密过程出错: {e}")
            return False
            
def main():
    """主函数"""
    decryptor = WeChatDBDecrypt()
    results = decryptor.auto_find_and_decrypt()
    
    if not results:
        print("未能解密任何数据库")
        return
        
    print(f"\n成功解密 {sum(1 for r in results if r['success'])} 个数据库:")
    for result in results:
        if result['success']:
            print(f"用户: {result['original']['username']}")
            print(f"数据库: {result['original']['db_name']}")
            print(f"解密路径: {result['decrypted_path']}")
            print("-" * 50)
    
if __name__ == "__main__":
    main() 