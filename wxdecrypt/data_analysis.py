"""
数据分析模块，提供数据可视化和词频分析功能
"""
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import jieba
from collections import Counter
from datetime import datetime
import wordcloud
import matplotlib.font_manager as fm
from typing import List, Dict, Any, Optional, Tuple, Union

# 检查是否有中文字体
def check_chinese_font():
    """检查系统中可用的中文字体"""
    chinese_fonts = []
    for f in fm.findSystemFonts():
        try:
            font = fm.FontProperties(fname=f)
            if font.get_name() and any([
                'simhei' in font.get_name().lower(),
                'microsoft yahei' in font.get_name().lower(),
                'simsun' in font.get_name().lower(),
                'nsimsun' in font.get_name().lower(),
                'kaiti' in font.get_name().lower(),
                'fangsong' in font.get_name().lower(),
                'STHeiti' in font.get_name(),
                'pingfang' in font.get_name().lower(),
                'heiti' in font.get_name().lower(),
                'songti' in font.get_name().lower(),
                'hei' in font.get_name().lower()
            ]):
                chinese_fonts.append(f)
        except:
            continue
    return chinese_fonts[0] if chinese_fonts else None

# 设置中文字体
CHINESE_FONT = check_chinese_font()
if CHINESE_FONT:
    plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=CHINESE_FONT).get_name()]
    plt.rcParams['axes.unicode_minus'] = False
else:
    print("警告: 未找到中文字体，图表中的中文可能无法正确显示")

def analyze_database(db_path: str, output_dir: str, is_qq: bool = False) -> Dict[str, Any]:
    """
    分析数据库，提取可视化和词频分析所需的数据
    
    Args:
        db_path: 数据库路径
        output_dir: 输出目录
        is_qq: 是否为QQ数据库
        
    Returns:
        Dict: 包含分析结果的字典
    """
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return {}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检测表结构
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        tables = [t[0] for t in tables]
        
        print(f"数据库中的表: {', '.join(tables)}")
        
        messages = []
        
        # 微信数据库通常有Message表
        if 'message' in [t.lower() for t in tables]:
            print("检测到微信消息表，开始读取数据...")
            # 检查表结构以确定正确的列名
            table_info = cursor.execute("PRAGMA table_info(message);").fetchall()
            column_names = [col[1] for col in table_info]
            
            # 典型的微信消息表结构
            if 'CreateTime' in column_names and 'Content' in column_names:
                query = """
                SELECT CreateTime, Content, Type, Status, IsSender FROM message
                WHERE Content IS NOT NULL AND Content != ''
                ORDER BY CreateTime
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    create_time, content, msg_type, status, is_sender = row
                    # 确保CreateTime是整数时间戳
                    try:
                        create_time = int(create_time)
                        create_time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        create_time_str = str(create_time)
                    
                    # 只处理文本消息
                    if msg_type == 1:  # 通常1表示文本消息
                        messages.append({
                            'timestamp': create_time,
                            'datetime': create_time_str,
                            'content': content,
                            'is_sender': bool(is_sender),
                            'type': msg_type
                        })
                
                print(f"成功读取 {len(messages)} 条消息")
        
        # QQ数据库表结构不同，需要适配
        elif 'msg' in [t.lower() for t in tables] and is_qq:
            print("检测到QQ消息表，开始读取数据...")
            # 检查表结构以确定正确的列名
            table_info = cursor.execute("PRAGMA table_info(msg);").fetchall()
            column_names = [col[1] for col in table_info]
            
            # 尝试识别QQ消息表结构（可能需要根据实际数据库调整）
            time_col = next((col for col in column_names if 'time' in col.lower()), None)
            content_col = next((col for col in column_names if 'content' in col.lower() or 'msg' in col.lower()), None)
            
            if time_col and content_col:
                query = f"""
                SELECT {time_col}, {content_col} FROM msg
                WHERE {content_col} IS NOT NULL AND {content_col} != ''
                ORDER BY {time_col}
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    time_val, content = row
                    try:
                        time_val = int(time_val)
                        time_str = datetime.fromtimestamp(time_val).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        time_str = str(time_val)
                    
                    messages.append({
                        'timestamp': time_val,
                        'datetime': time_str,
                        'content': content,
                        'is_sender': None,  # QQ数据可能无法确定
                        'type': None
                    })
                
                print(f"成功读取 {len(messages)} 条消息")
        
        conn.close()
        
        # 如果有消息数据，进行分析
        if messages:
            return {
                'messages': messages,
                'db_path': db_path,
                'output_dir': output_dir
            }
        else:
            print("未找到消息数据")
            return {}
        
    except Exception as e:
        print(f"分析数据库时出错: {e}")
        return {}

def create_visualizations(analysis_data: Dict[str, Any], output_dir: str) -> None:
    """
    创建数据可视化图表
    
    Args:
        analysis_data: 分析数据
        output_dir: 输出目录
    """
    if not analysis_data or 'messages' not in analysis_data:
        print("没有足够的数据用于可视化")
        return
    
    messages = analysis_data['messages']
    os.makedirs(output_dir, exist_ok=True)
    
    # 转换为pandas数据框以便分析
    df = pd.DataFrame(messages)
    
    # 1. 按日期统计消息数量
    if 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.date
        messages_by_date = df.groupby('date').size()
        
        plt.figure(figsize=(12, 6))
        messages_by_date.plot(kind='line')
        plt.title('每日消息数量')
        plt.xlabel('日期')
        plt.ylabel('消息数量')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '每日消息数量.png'), dpi=300)
        print(f"已生成每日消息数量图表: {os.path.join(output_dir, '每日消息数量.png')}")
        plt.close()
        
        # 2. 按小时统计消息数量
        df['hour'] = pd.to_datetime(df['timestamp'], unit='s').dt.hour
        messages_by_hour = df.groupby('hour').size()
        
        plt.figure(figsize=(10, 6))
        messages_by_hour.plot(kind='bar')
        plt.title('各时段消息数量')
        plt.xlabel('小时')
        plt.ylabel('消息数量')
        plt.xticks(range(24))
        plt.grid(True, linestyle='--', alpha=0.7, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '各时段消息数量.png'), dpi=300)
        print(f"已生成各时段消息数量图表: {os.path.join(output_dir, '各时段消息数量.png')}")
        plt.close()
    
    # 3. 按消息类型统计（如果有类型信息）
    if 'type' in df.columns and df['type'].notna().any():
        messages_by_type = df.groupby('type').size()
        
        plt.figure(figsize=(8, 8))
        messages_by_type.plot(kind='pie', autopct='%1.1f%%')
        plt.title('消息类型分布')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '消息类型分布.png'), dpi=300)
        print(f"已生成消息类型分布图表: {os.path.join(output_dir, '消息类型分布.png')}")
        plt.close()
    
    # 4. 按发送方统计（如果有发送方信息）
    if 'is_sender' in df.columns and df['is_sender'].notna().any():
        messages_by_sender = df.groupby('is_sender').size()
        
        plt.figure(figsize=(8, 8))
        messages_by_sender.plot(kind='pie', labels=['接收', '发送'], autopct='%1.1f%%')
        plt.title('发送/接收消息比例')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '发送接收比例.png'), dpi=300)
        print(f"已生成发送接收比例图表: {os.path.join(output_dir, '发送接收比例.png')}")
        plt.close()

def generate_word_frequency(analysis_data: Dict[str, Any], output_dir: str, 
                           top_n: int = 100, generate_wordcloud: bool = True) -> Dict[str, int]:
    """
    生成词频分析
    
    Args:
        analysis_data: 分析数据
        output_dir: 输出目录
        top_n: 返回前N个高频词
        generate_wordcloud: 是否生成词云图
        
    Returns:
        Dict: 词频统计结果
    """
    if not analysis_data or 'messages' not in analysis_data:
        print("没有足够的数据用于词频分析")
        return {}
    
    messages = analysis_data['messages']
    os.makedirs(output_dir, exist_ok=True)
    
    # 提取所有文本内容
    all_text = " ".join([msg['content'] for msg in messages if msg['content']])
    
    # 使用jieba进行分词
    jieba.setLogLevel(20)  # 设置jieba的日志级别为INFO，减少输出
    words = jieba.cut(all_text, cut_all=False)
    
    # 过滤停用词
    stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', 
                   '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', 
                   '着', '没有', '看', '好', '自己', '这', '这个', '那', '那个',
                   '。', ',', '?', '!', '、', ':', '"', '"', "'", "'", '(', ')',
                   '[', ']', '{', '}', '[', ']', '<', '>', ':', ';', '"', '...',
                   '\n', '\t', '\r', ' ', '+', '-', '*', '/', '='])
    
    filtered_words = [word for word in words if len(word) > 1 and word not in stopwords]
    
    # 统计词频
    word_freq = Counter(filtered_words)
    
    # 获取前N个高频词
    top_words = word_freq.most_common(top_n)
    
    # 保存词频统计结果到文件
    with open(os.path.join(output_dir, '词频统计.txt'), 'w', encoding='utf-8') as f:
        f.write(f"词频统计 (Top {top_n}):\n")
        f.write("="*30 + "\n")
        for word, freq in top_words:
            f.write(f"{word}: {freq}\n")
    
    print(f"已生成词频统计文件: {os.path.join(output_dir, '词频统计.txt')}")
    
    # 生成词频统计图表
    words, freqs = zip(*top_words[:30])  # 图表中只显示前30个词
    
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(words)), freqs, align='center')
    plt.yticks(range(len(words)), words)
    plt.xlabel('频率')
    plt.title('词频统计 (Top 30)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '词频统计.png'), dpi=300)
    print(f"已生成词频统计图表: {os.path.join(output_dir, '词频统计.png')}")
    plt.close()
    
    # 生成词云图
    if generate_wordcloud:
        try:
            wc = wordcloud.WordCloud(
                font_path=CHINESE_FONT if CHINESE_FONT else None,
                width=800, height=600,
                background_color='white',
                max_words=200,
                max_font_size=150,
                random_state=42
            )
            wc.generate_from_frequencies(dict(top_words))
            
            plt.figure(figsize=(10, 8))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, '词云图.png'), dpi=300)
            print(f"已生成词云图: {os.path.join(output_dir, '词云图.png')}")
            plt.close()
        except Exception as e:
            print(f"生成词云图时出错: {e}")
    
    return dict(top_words)

def analyze_decrypted_database(db_path: str, output_dir: str = None, is_qq: bool = False) -> None:
    """
    分析已解密的数据库，生成可视化和词频分析
    
    Args:
        db_path: 数据库路径
        output_dir: 输出目录，若为None则使用数据库所在目录
        is_qq: 是否为QQ数据库
    """
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(db_path), 'analysis')
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始分析数据库: {db_path}")
    print(f"分析结果将保存到: {output_dir}")
    
    # 分析数据库
    analysis_data = analyze_database(db_path, output_dir, is_qq)
    
    if not analysis_data:
        print("分析失败，无法继续")
        return
    
    # 创建可视化
    create_visualizations(analysis_data, output_dir)
    
    # 生成词频分析
    generate_word_frequency(analysis_data, output_dir, top_n=100)
    
    print(f"分析完成！所有结果已保存到: {output_dir}")

def generate_analysis_report(db_path: str, output_dir: str, is_qq: bool = False) -> None:
    """
    生成分析报告，包括可视化和词频分析
    
    Args:
        db_path: 数据库路径
        output_dir: 输出目录
        is_qq: 是否为QQ数据库
    """
    analyze_decrypted_database(db_path, output_dir, is_qq)
    
    # 生成HTML报告
    report_path = os.path.join(output_dir, 'analysis_report.html')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>聊天记录分析报告</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                .visualization {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .visualization img {{
                    max-width: 100%;
                    border: 1px solid #ddd;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    color: #777;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>聊天记录分析报告</h1>
                <p>数据库路径: {db_path}</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>数据可视化</h2>
                
                <div class="visualization">
                    <h3>每日消息数量</h3>
                    <img src="每日消息数量.png" alt="每日消息数量" />
                </div>
                
                <div class="visualization">
                    <h3>各时段消息数量</h3>
                    <img src="各时段消息数量.png" alt="各时段消息数量" />
                </div>
                
                <div class="visualization">
                    <h3>词频统计</h3>
                    <img src="词频统计.png" alt="词频统计" />
                </div>
                
                <div class="visualization">
                    <h3>词云图</h3>
                    <img src="词云图.png" alt="词云图" />
                </div>
                
                <div class="footer">
                    <p>由微信/QQ数据库解密与分析工具生成</p>
                </div>
            </div>
        </body>
        </html>
        """)
    
    print(f"已生成分析报告: {report_path}")
    return report_path

if __name__ == "__main__":
    # 测试
    db_path = input("请输入已解密的数据库路径: ")
    if os.path.exists(db_path):
        output_dir = os.path.join(os.path.dirname(db_path), 'analysis')
        is_qq = "qq" in db_path.lower() or input("是否为QQ数据库? (y/n): ").lower() == 'y'
        generate_analysis_report(db_path, output_dir, is_qq)
    else:
        print("文件不存在!") 