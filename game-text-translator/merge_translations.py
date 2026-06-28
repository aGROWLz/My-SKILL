# -*- coding: utf-8 -*-
"""
合并翻译结果
自适应目录：根据输入文件路径自动找到 Trans/<文件名>/ 目录
"""

import json
import os
import sys
import glob

def get_trans_dir(input_file):
    """根据输入文件路径获取翻译目录"""
    input_dir = os.path.dirname(os.path.abspath(input_file))
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    trans_dir = os.path.join(input_dir, "Trans", file_name)
    return trans_dir, file_name

def merge_translations(input_file):
    """合并所有翻译批次"""
    
    # 获取翻译目录
    trans_dir, file_name = get_trans_dir(input_file)
    translated_dir = os.path.join(trans_dir, "translated")
    output_file = os.path.join(trans_dir, f"{file_name}_CN.json")
    
    if not os.path.exists(translated_dir):
        print(f"错误: 找不到翻译目录 {translated_dir}")
        return
    
    # 查找所有翻译文件
    pattern = os.path.join(translated_dir, "translated_*.json")
    files = sorted(glob.glob(pattern))
    
    if not files:
        print("未找到翻译文件 (translated_*.json)")
        return
    
    print(f"找到 {len(files)} 个翻译文件")
    
    # 合并所有翻译
    merged = {}
    for file_path in files:
        print(f"正在合并: {os.path.basename(file_path)}")
        with open(file_path, 'r', encoding='utf-8') as f:
            batch = json.load(f)
            merged.update(batch)
    
    print(f"\n合并完成，共 {len(merged)} 条")
    
    # 保存合并结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=4)
    
    print(f"已保存到: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python merge_translations.py <游戏文件路径>")
        print("示例: python merge_translations.py ManualTransFile.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.isabs(input_file):
        input_file = os.path.abspath(input_file)
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        sys.exit(1)
    
    merge_translations(input_file)
