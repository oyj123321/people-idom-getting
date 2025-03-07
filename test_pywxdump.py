"""
测试PyWxDump模块
"""

import sys
import os

print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

print("\n尝试导入PyWxDump:")
try:
    import PyWxDump
    print(f"PyWxDump版本: {getattr(PyWxDump, '__version__', '未知')}")
    print(f"PyWxDump路径: {PyWxDump.__file__}")
    
    print("\n尝试导入wx子模块:")
    try:
        from PyWxDump import wx
        print(f"wx模块路径: {wx.__file__}")
        
        print("\n尝试导入解密函数:")
        try:
            from PyWxDump.wx import get_key, decode_database
            print("成功导入get_key和decode_database函数")
        except ImportError as e:
            print(f"导入解密函数失败: {e}")
    except ImportError as e:
        print(f"导入wx子模块失败: {e}")
except ImportError as e:
    print(f"导入PyWxDump失败: {e}")

print("\n检查真实解密模块:")
try:
    from wxdecrypt.real_decrypt import RealWeChatDBDecrypt, HAS_PYWXDUMP
    print(f"RealWeChatDBDecrypt类可用: {RealWeChatDBDecrypt is not None}")
    print(f"HAS_PYWXDUMP标志: {HAS_PYWXDUMP}")
except ImportError as e:
    print(f"导入真实解密模块失败: {e}") 