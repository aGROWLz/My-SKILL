import json
import os
import sys

def fix_translation_keys(source_file_path):
    source_dir = os.path.dirname(source_file_path)
    source_name = os.path.splitext(os.path.basename(source_file_path))[0]
    
    trans_dir = os.path.join(source_dir, 'Trans', source_name)
    batches_dir = os.path.join(trans_dir, 'batches')
    translated_dir = os.path.join(trans_dir, 'translated')
    
    if not os.path.exists(batches_dir) or not os.path.exists(translated_dir):
        print("错误：批次目录或翻译目录不存在")
        return
    
    batch_files = sorted([f for f in os.listdir(batches_dir) if f.startswith('batch_')])
    
    total_fixed = 0
    
    for batch_file in batch_files:
        batch_path = os.path.join(batches_dir, batch_file)
        translated_path = os.path.join(translated_dir, f'translated_{batch_file[6:-5]}.json')
        
        if not os.path.exists(translated_path):
            print(f"跳过：{translated_path} 不存在")
            continue
        
        with open(batch_path, 'r', encoding='utf-8') as f:
            original = json.load(f)
        
        with open(translated_path, 'r', encoding='utf-8') as f:
            translated = json.load(f)
        
        orig_keys = set(original.keys())
        trans_keys = set(translated.keys())
        
        missing_keys = orig_keys - trans_keys
        extra_keys = trans_keys - orig_keys
        
        if not missing_keys and not extra_keys:
            print(f"{batch_file}: 无需修复")
            continue
        
        fixed = {}
        fixed_count = 0
        
        for orig_key in original:
            if orig_key in translated:
                fixed[orig_key] = translated[orig_key]
            else:
                found = False
                for trans_key in translated:
                    if trans_key == orig_key:
                        fixed[orig_key] = translated[trans_key]
                        found = True
                        break
                
                if not found:
                    for trans_key in list(translated.keys()):
                        if trans_key != orig_key:
                            fixed[orig_key] = translated[trans_key]
                            del translated[trans_key]
                            fixed_count += 1
                            found = True
                            break
                
                if not found:
                    fixed[orig_key] = original[orig_key]
                    fixed_count += 1
                    print(f"  警告：未找到键 '{orig_key}' 的翻译")
        
        with open(translated_path, 'w', encoding='utf-8') as f:
            json.dump(fixed, f, ensure_ascii=False, indent=2)
        
        print(f"修复 {batch_file}: 修正了 {fixed_count} 个键")
        total_fixed += fixed_count
    
    print(f"\n共修复了 {total_fixed} 个键")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python fix_translation_keys.py <源文件路径>")
        sys.exit(1)
    
    fix_translation_keys(sys.argv[1])