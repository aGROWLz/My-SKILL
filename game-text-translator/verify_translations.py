# -*- coding: utf-8 -*-
"""
验证翻译完整性
支持两种模式：
1. 完整验证：python verify_translations.py <游戏文件路径>
2. 单批次验证：python verify_translations.py <批次文件.json> <译文.json>
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

def verify_single_batch(batch_file, translated_file):
    """验证单个批次的翻译完整性"""
    
    print("=" * 60)
    print("单批次翻译验证")
    print("=" * 60)
    
    # 读取原文
    if not os.path.exists(batch_file):
        print(f"错误: 找不到批次文件 {batch_file}")
        return False
    
    # 读取译文
    if not os.path.exists(translated_file):
        print(f"错误: 找不到译文文件 {translated_file}")
        return False
    
    with open(batch_file, 'r', encoding='utf-8') as f:
        original = json.load(f)
    with open(translated_file, 'r', encoding='utf-8') as f:
        translated = json.load(f)
    
    print(f"\n【文件信息】")
    print(f"批次文件: {os.path.basename(batch_file)}")
    print(f"译文文件: {os.path.basename(translated_file)}")
    
    # 对比条目
    original_keys = set(original.keys())
    translated_keys = set(translated.keys())
    
    missing_keys = original_keys - translated_keys
    extra_keys = translated_keys - original_keys
    
    print(f"\n【条目统计】")
    print(f"原文条目: {len(original)}")
    print(f"译文条目: {len(translated)}")
    
    # 输出遗漏条目
    if missing_keys:
        print(f"\n❌ 遗漏 {len(missing_keys)} 条:")
        missing_entries = {}
        for i, key in enumerate(sorted(missing_keys)):
            if i < 10:
                print(f"   - {key}")
            missing_entries[key] = original[key]
        if len(missing_keys) > 10:
            print(f"   ... 还有 {len(missing_keys) - 10} 条")
        
        # 保存遗漏内容
        batch_num = os.path.basename(batch_file).replace("batch_", "").replace(".json", "")
        missing_dir = os.path.join(os.path.dirname(batch_file), "..", "missing")
        os.makedirs(missing_dir, exist_ok=True)
        missing_file = os.path.join(missing_dir, f"missing_{batch_num}.json")
        with open(missing_file, 'w', encoding='utf-8') as f:
            json.dump(missing_entries, f, ensure_ascii=False, indent=4)
        print(f"\n遗漏内容已保存到: {missing_file}")
    else:
        print(f"\n✅ 无遗漏条目")
    
    if extra_keys:
        print(f"\n⚠️  多出 {len(extra_keys)} 条")
    
    # 汇总
    print(f"\n【汇总】")
    if missing_keys:
        print(f"验证失败: 遗漏 {len(missing_keys)} 条")
        return False
    else:
        print(f"验证通过: 所有条目都已翻译")
        return True

def verify_all_translations(input_file):
    """验证所有翻译的完整性"""
    
    # 获取翻译目录
    trans_dir, file_name = get_trans_dir(input_file)
    batch_dir = os.path.join(trans_dir, "batches")
    translated_dir = os.path.join(trans_dir, "translated")
    missing_dir = os.path.join(trans_dir, "missing")
    
    # 创建遗漏目录
    os.makedirs(missing_dir, exist_ok=True)
    
    # 查找所有原文文件和翻译文件
    original_files = sorted(glob.glob(os.path.join(batch_dir, "batch_*.json")))
    translated_files = sorted(glob.glob(os.path.join(translated_dir, "translated_*.json")))
    
    print("=" * 60)
    print("翻译完整性验证报告")
    print("=" * 60)
    
    # 过滤掉 _withlines 文件
    original_files = [f for f in original_files if '_withlines' not in os.path.basename(f)]
    
    # 检查文件数量
    print(f"\n【文件统计】")
    print(f"原文文件数量: {len(original_files)}")
    print(f"翻译文件数量: {len(translated_files)}")
    
    if len(translated_files) < len(original_files):
        missing = len(original_files) - len(translated_files)
        print(f"⚠️  警告: 缺少 {missing} 个翻译文件")
    
    # 提取文件编号
    original_nums = set()
    for f in original_files:
        num = os.path.basename(f).replace("batch_", "").replace(".json", "")
        original_nums.add(num)
    
    translated_nums = set()
    for f in translated_files:
        num = os.path.basename(f).replace("translated_", "").replace(".json", "")
        translated_nums.add(num)
    
    # 找出缺失的翻译
    missing_translations = original_nums - translated_nums
    extra_translations = translated_nums - original_nums
    
    if missing_translations:
        print(f"\n【缺失的翻译文件】")
        for num in sorted(missing_translations):
            print(f"  ❌ translated_{num}.json")
    
    if extra_translations:
        print(f"\n【多余的翻译文件】")
        for num in sorted(extra_translations):
            print(f"  ⚠️  translated_{num}.json (没有对应的原文)")
    
    # 逐个对比条目
    print(f"\n【条目对比】")
    total_original = 0
    total_translated = 0
    all_missing_keys = []
    batch_missing_summary = {}
    
    for orig_file in original_files:
        num = os.path.basename(orig_file).replace("batch_", "").replace(".json", "")
        trans_file = os.path.join(translated_dir, f"translated_{num}.json")
        
        if not os.path.exists(trans_file):
            # 整个批次都缺失，记录所有条目
            with open(orig_file, 'r', encoding='utf-8') as f:
                original = json.load(f)
            total_original += len(original)
            for key, value in original.items():
                all_missing_keys.append((num, key, value))
            batch_missing_summary[num] = list(original.keys())
            print(f"  batch_{num}: ❌ 整个批次缺失 ({len(original)} 条)")
            continue
        
        # 读取原文和翻译
        with open(orig_file, 'r', encoding='utf-8') as f:
            original = json.load(f)
        with open(trans_file, 'r', encoding='utf-8') as f:
            translated = json.load(f)
        
        total_original += len(original)
        total_translated += len(translated)
        
        # 对比条目
        original_keys = set(original.keys())
        translated_keys = set(translated.keys())
        
        missing_keys = original_keys - translated_keys
        extra_keys = translated_keys - original_keys
        
        if missing_keys or extra_keys:
            print(f"\n  batch_{num}:")
            print(f"    原文: {len(original)} 条, 翻译: {len(translated)} 条")
            
            if missing_keys:
                print(f"    ❌ 遗漏 {len(missing_keys)} 条:")
                batch_missing_summary[num] = []
                for key in missing_keys:
                    all_missing_keys.append((num, key, original[key]))
                    batch_missing_summary[num].append(key)
                    if len(batch_missing_summary[num]) <= 5:
                        print(f"       - {key}")
                if len(batch_missing_summary[num]) > 5:
                    print(f"       ... 还有 {len(batch_missing_summary[num]) - 5} 条")
            
            if extra_keys:
                print(f"    ⚠️  多出 {len(extra_keys)} 条")
        else:
            print(f"  batch_{num}: ✅ 完整 ({len(original)} 条)")
    
    # 保存遗漏内容到 missing 目录
    print(f"\n【保存遗漏内容】")
    for num, missing_keys_list in batch_missing_summary.items():
        # 读取原文
        orig_file = os.path.join(batch_dir, f"batch_{num}.json")
        with open(orig_file, 'r', encoding='utf-8') as f:
            original = json.load(f)
        
        # 提取遗漏的条目
        missing_entries = {}
        for key in missing_keys_list:
            if key in original:
                missing_entries[key] = original[key]
        
        # 保存到 missing 目录
        missing_file = os.path.join(missing_dir, f"missing_{num}.json")
        with open(missing_file, 'w', encoding='utf-8') as f:
            json.dump(missing_entries, f, ensure_ascii=False, indent=4)
        print(f"  已保存: missing_{num}.json ({len(missing_entries)} 条)")
    
    # 保存汇总报告
    report_file = os.path.join(missing_dir, "missing_report.json")
    report = {
        "total_original": total_original,
        "total_translated": total_translated,
        "total_missing": len(all_missing_keys),
        "missing_details": {}
    }
    for num, key, value in all_missing_keys:
        if num not in report["missing_details"]:
            report["missing_details"][num] = []
        report["missing_details"][num].append({
            "key": key,
            "original_value": value
        })
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    print(f"\n  汇总报告已保存到: missing_report.json")
    
    # 汇总
    print(f"\n【汇总】")
    print(f"原文总条目: {total_original}")
    print(f"翻译总条目: {total_translated}")
    print(f"遗漏条目数: {len(all_missing_keys)}")
    
    if all_missing_keys:
        print(f"\n⚠️  共遗漏 {len(all_missing_keys)} 条，遗漏内容已保存到 missing 目录")
        print(f"请补充翻译后重新验证")
        return False
    else:
        print(f"\n✅ 翻译完整，所有条目都已翻译")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  完整验证: python verify_translations.py <游戏文件路径>")
        print("  单批次验证: python verify_translations.py <批次文件.json> <译文.json>")
        print("")
        print("示例:")
        print("  python verify_translations.py ManualTransFile.json")
        print("  python verify_translations.py batch_001.json translated_001.json")
        sys.exit(1)
    
    if len(sys.argv) == 3:
        # 单批次验证模式
        batch_file = sys.argv[1]
        translated_file = sys.argv[2]
        
        if not os.path.isabs(batch_file):
            batch_file = os.path.abspath(batch_file)
        if not os.path.isabs(translated_file):
            translated_file = os.path.abspath(translated_file)
        
        verify_single_batch(batch_file, translated_file)
    else:
        # 完整验证模式
        input_file = sys.argv[1]
        
        if not os.path.isabs(input_file):
            input_file = os.path.abspath(input_file)
        
        if not os.path.exists(input_file):
            print(f"错误: 找不到输入文件 {input_file}")
            sys.exit(1)
        
        verify_all_translations(input_file)
