# -*- coding: utf-8 -*-
"""
将日文条目分批导出
自适应目录：根据输入文件路径自动找到 Trans/<文件名>/ 目录
"""

import json
import os
import sys

def get_trans_dir(input_file):
    """根据输入文件路径获取翻译目录"""
    input_dir = os.path.dirname(os.path.abspath(input_file))
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    trans_dir = os.path.join(input_dir, "Trans", file_name)
    return trans_dir, file_name

def split_into_batches(input_file, batch_size=200):
    """将日文条目分批导出"""
    
    # 获取翻译目录
    trans_dir, file_name = get_trans_dir(input_file)
    
    # 输入文件路径
    input_json = os.path.join(trans_dir, f"{file_name}_Japanese.json")
    input_with_lines = os.path.join(trans_dir, f"{file_name}_Japanese_WithLines.json")
    output_dir = os.path.join(trans_dir, "batches")
    
    if not os.path.exists(input_json):
        print(f"错误: 找不到文件 {input_json}")
        print("请先运行 extract_japanese.py")
        return
    
    # 读取日文条目
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 读取带行号的版本
    with open(input_with_lines, 'r', encoding='utf-8') as f:
        data_with_lines = json.load(f)
    
    entries = list(data.items())
    total = len(entries)
    num_batches = (total + batch_size - 1) // batch_size
    
    print(f"总条目数: {total}")
    print(f"每批大小: {batch_size}")
    print(f"批次数: {num_batches}")
    print(f"输出目录: {output_dir}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 分批导出
    for i in range(num_batches):
        start = i * batch_size
        end = min((i + 1) * batch_size, total)
        batch = dict(entries[start:end])
        
        # 获取本批次的键
        batch_keys = list(batch.keys())
        
        # 导出为JSON（用于翻译）
        output_file = os.path.join(output_dir, f"batch_{i+1:03d}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
        
        # 导出带行号的JSON（用于定位和替换）
        output_with_lines_file = os.path.join(output_dir, f"batch_{i+1:03d}_withlines.json")
        batch_with_lines = {}
        for key in batch_keys:
            if key in data_with_lines:
                batch_with_lines[key] = data_with_lines[key]
        with open(output_with_lines_file, 'w', encoding='utf-8') as f:
            json.dump(batch_with_lines, f, ensure_ascii=False, indent=2)
        
        # 导出为方便翻译的文本格式
        text_file = os.path.join(output_dir, f"batch_{i+1:03d}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 第 {i+1} 批 (条目 {start+1}-{end}) ===\n\n")
            for j, key in enumerate(batch_keys, 1):
                info = data_with_lines.get(key, {})
                line_num = info.get('line', '?')
                f.write(f"[{start+j}] 行{line_num}: {key}\n")
        
        print(f"已导出: batch_{i+1:03d}.json ({end-start} 条)")
    
    # 创建索引文件
    index_file = os.path.join(output_dir, "index.txt")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f"日文条目分批导出索引\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"总条目数: {total}\n")
        f.write(f"每批大小: {batch_size}\n")
        f.write(f"批次数: {num_batches}\n\n")
        f.write(f"文件说明:\n")
        f.write(f"  batch_XXX.json        - 原文（用于翻译）\n")
        f.write(f"  batch_XXX_withlines.json - 带行号版本（用于定位替换）\n")
        f.write(f"  batch_XXX.txt         - 文本格式（方便查看）\n")
    
    print(f"\n索引文件已保存到: {index_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python split_batches.py <游戏文件路径>")
        print("示例: python split_batches.py ManualTransFile.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.isabs(input_file):
        input_file = os.path.abspath(input_file)
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        sys.exit(1)
    
    split_into_batches(input_file)
