# 微信/QQ数据库自动识别与解密工具

这是一个简单的工具，用于自动识别微信和QQ的数据库位置，并进行解密。

## 功能特点

- 自动识别微信数据库位置
- 自动从内存中获取数据库密钥
- 解密数据库并保存到指定位置
- 支持多用户的微信数据库
- 简单易用的命令行界面

## 安装方法

```bash
# 克隆仓库
git clone https://github.com/username/wxdecrypt.git
cd wxdecrypt

# 安装依赖
pip install -e .
```

## 使用方法

### 列出已发现的数据库

```bash
wxdecrypt -l
```

### 解密所有发现的数据库

```bash
wxdecrypt -o ./解密结果
```

### 显示帮助信息

```bash
wxdecrypt -h
```

## 注意事项

1. 本工具仅用于合法用途，如数据备份、数据迁移等
2. 使用前请确保微信/QQ已经正常启动并登录
3. 当前版本仅支持Windows系统
4. QQ数据库解密功能尚未实现

## 原理简介

本工具基于以下原理实现：

1. 通过读取注册表获取微信安装位置和数据文件位置
2. 读取运行中的微信进程内存获取数据库密钥
3. 使用密钥解密原始数据库并保存到新位置

## 感谢

本项目参考了以下开源项目：

- [PyWxDump](https://github.com/xaoyaoo/PyWxDump)
- [wechat-db-decrypt](https://github.com/zzyzhangziyu/wechat-db-decrypt)

## 许可证

MIT 