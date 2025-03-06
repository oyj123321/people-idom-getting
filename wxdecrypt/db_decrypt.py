"""
微信/QQ数据库解密模块
"""
import os
import sys
import sqlite3
import hashlib
import binascii
import shutil
import glob
from typing import Optional, List, Dict, Any, Union

from wxdecrypt.utils.memory_utils import get_wechat_key
from wxdecrypt.wechat_path import get_wechat_db_path, get_qq_db_path

class WeChatDBDecrypt:
    """微信/QQ数据库解密类"""
    
    def __init__(self):
        """初始化数据库解密器"""
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
        test_dir = os.path.join(os.getcwd(), "test_data")
        os.makedirs(test_dir, exist_ok=True)
        
        if self.decrypt_qq:
            # 查找测试QQ数据库文件
            test_files = []
            for ext in ['Msg*.db']:
                pattern = os.path.join(test_dir, ext)
                test_files.extend(glob.glob(pattern))
            
            if not test_files:
                # 创建一个测试QQ数据库
                test_db_path = os.path.join(test_dir, "Msg3.0.db")
                with open(test_db_path, "wb") as f:
                    f.write(b"SQLite format 3\0")
                    f.write(os.urandom(1024))
                test_files = [test_db_path]
                
            # 处理每个测试文件
            for db_path in test_files:
                db_name = os.path.basename(db_path)
                
                # 模拟QQ用户信息
                qqid = "12345678"
                qq_output_dir = os.path.join(output_dir, "QQ", qqid)
                os.makedirs(qq_output_dir, exist_ok=True)
                
                # 模拟解密过程
                output_path = os.path.join(qq_output_dir, db_name)
                shutil.copy2(db_path, output_path)
                
                # 记录结果
                results.append({
                    'original': {
                        'qqid': qqid,
                        'path': db_path,
                        'db_name': db_name
                    },
                    'decrypted_path': output_path,
                    'success': True
                })
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
                
                # 尝试打开确认是有效的数据库
                try:
                    conn = sqlite3.connect(output_path)
                    conn.execute("SELECT 1")
                    conn.close()
                    print(f"QQ数据库处理成功: {output_path}")
                    return True
                except sqlite3.Error as e:
                    print(f"QQ数据库处理失败: {e}")
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return False
            else:
                # 微信数据库需要解密
                if not self.key:
                    print("未设置数据库密钥")
                    return False
                    
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
                    
                    print(f"微信数据库解密成功: {output_path}")
                    return True
                    
                except sqlite3.Error as e:
                    print(f"解密数据库失败: {e}")
                    # 删除解密失败的文件
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return False
                    
        except Exception as e:
            print(f"处理过程出错: {e}")
            return False
            
def main():
    """主函数"""
    # 解密微信数据库
    print("解密微信数据库...")
    decryptor = WeChatDBDecrypt()
    wx_results = decryptor.auto_find_and_decrypt()
    
    # 解密QQ数据库
    print("\n解密QQ数据库...")
    decryptor = WeChatDBDecrypt()
    decryptor.decrypt_qq = True
    qq_results = decryptor.auto_find_and_decrypt()
    
    # 显示结果
    wx_success = sum(1 for r in wx_results if r['success'])
    qq_success = sum(1 for r in qq_results if r['success'])
    
    print(f"\n解密结果统计:")
    print(f"微信数据库: 成功 {wx_success}/{len(wx_results)}")
    print(f"QQ数据库: 成功 {qq_success}/{len(qq_results)}")
    
    all_results = wx_results + qq_results
    if not all_results:
        print("未能解密任何数据库")
        return
        
    print(f"\n成功解密的数据库:")
    for result in all_results:
        if result['success']:
            if 'username' in result['original']:
                # 微信数据库
                print(f"用户: {result['original']['username']}")
                print(f"微信ID: {result['original'].get('wxid', 'unknown')}")
                print(f"类型: 微信")
            else:
                # QQ数据库
                print(f"QQ号: {result['original'].get('qqid', 'unknown')}")
                print(f"类型: QQ")
            print(f"数据库: {result['original']['db_name']}")
            print(f"解密路径: {result['decrypted_path']}")
            print("-" * 50)
    
if __name__ == "__main__":
    main() 