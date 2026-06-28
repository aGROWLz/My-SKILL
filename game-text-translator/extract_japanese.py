# -*- coding: utf-8 -*-
"""
从游戏文件中提取日文内容
自适应目录：根据输入文件路径自动创建 Trans/<文件名>/ 目录
"""

import json
import re
import os
import sys

def contains_japanese(text):
    """检查文本是否包含日文字符（平假名、片假名、汉字）"""
    if not isinstance(text, str):
        return False
    pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF]')
    return bool(pattern.search(text))

def get_trans_dir(input_file):
    """根据输入文件路径获取翻译目录"""
    # 获取输入文件的目录和文件名
    input_dir = os.path.dirname(os.path.abspath(input_file))
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # 翻译目录：输入文件所在目录/Trans/<文件名>/
    trans_dir = os.path.join(input_dir, "Trans", file_name)
    
    return trans_dir, file_name

def extract_japanese_entries(input_file):
    """提取日文条目，并记录行号"""
    
    print(f"正在读取文件: {input_file}")
    
    # 获取翻译目录
    trans_dir, file_name = get_trans_dir(input_file)
    os.makedirs(trans_dir, exist_ok=True)
    
    print(f"翻译目录: {trans_dir}")
    
    # 逐行解析，记录行号
    japanese_entries = {}
    japanese_entries_with_lines = {}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"总行数: {len(lines)}")
    
    # 使用正则表达式匹配键值对
    pattern = re.compile(r'^\s*"([^"]+)"\s*:\s*"([^"]*)"')
    
    for line_num, line in enumerate(lines, 1):
        match = pattern.match(line)
        if match:
            key = match.group(1)
            value = match.group(2)
            
            # 检查键和值是否都包含日文
            if contains_japanese(key) and contains_japanese(value):
                japanese_entries[key] = value
                japanese_entries_with_lines[key] = {
                    "value": value,
                    "line": line_num
                }
    
    print(f"日文条目数: {len(japanese_entries)}")
    
    # 输出文件路径
    output_file = os.path.join(trans_dir, f"{file_name}_Japanese.json")
    output_with_lines_file = os.path.join(trans_dir, f"{file_name}_Japanese_WithLines.json")
    
    # 保存结果（标准格式，用于翻译）
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(japanese_entries, f, ensure_ascii=False, indent=4)
    
    # 保存带行号的结果（用于后续替换）
    with open(output_with_lines_file, 'w', encoding='utf-8') as f:
        json.dump(japanese_entries_with_lines, f, ensure_ascii=False, indent=4)
    
    print(f"已保存到: {output_file}")
    print(f"带行号版本已保存到: {output_with_lines_file}")
    
    # 显示一些示例
    print("\n=== 示例条目（前10个）===")
    for i, (key, info) in enumerate(list(japanese_entries_with_lines.items())[:10]):
        print(f"行 {info['line']}: {key}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python extract_japanese.py <游戏文件路径>")
        print("示例: python extract_japanese.py ManualTransFile.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(input_file):
        input_file = os.path.abspath(input_file)
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        sys.exit(1)
    
    extract_japanese_entries(input_file)
