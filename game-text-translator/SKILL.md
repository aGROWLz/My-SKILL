---
name: "game-text-translator"
description: "游戏文本翻译工作流 - 从游戏文件提取日文、分批、翻译、验证、合并。当用户需要翻译游戏文本时调用，大模型必须亲自翻译。"
---

# 游戏文本翻译工作流

本技能用于翻译游戏文本文件。**大模型必须亲自翻译，禁止调用外部翻译API或脚本。**

## 重要规则

1. **大模型亲自翻译**：必须由大模型自己翻译，不能调用外部翻译服务
2. **自适应目录**：脚本自动检测当前工作目录，翻译产物放在当前项目的 `Trans/` 目录下
3. **保持格式**：只翻译值的内容，保持 JSON 格式不变
4. **并行翻译（强制）**：必须使用子代理并行翻译多个批次，提高效率

## 目录结构（自适应）

脚本会自动检测当前工作目录，生成如下结构：

```
<当前项目目录>/
└── Trans/
    └── <游戏文件名>/
        ├── <游戏文件名>_Japanese.json
        ├── <游戏文件名>_Japanese_WithLines.json
        ├── <游戏文件名>_CN.json          # 最终翻译结果
        ├── batches/                      # 原文分批
        ├── translated/                   # 翻译结果
        └── missing/                      # 遗漏内容
```

## 工作流程

### 步骤 1：提取日文内容

询问用户游戏文件路径，然后运行：

```bash
python <skill目录>/extract_japanese.py <游戏文件路径>
```

脚本会自动：
- 检测游戏文件路径
- 在游戏文件所在目录的父目录创建 `Trans/<游戏文件名>/` 目录
- 提取日文条目并记录行号

### 步骤 2：分批导出

```bash
python <skill目录>/split_batches.py <游戏文件路径>
```

输出到 `Trans/<游戏文件名>/batches/`

### 步骤 3：大模型亲自翻译（强制使用子代理并行）

**必须使用 Task 工具的 general_purpose_task 子代理并行翻译多个批次。**

#### 并行翻译规则：

1. **每次并行启动多个子代理**（建议 3-5 个）
2. **每个子代理负责翻译 3 个批次**
3. **子代理独立完成翻译并保存结果**
4. **主代理等待所有子代理完成后继续**

#### 并行翻译示例：

```
主代理同时发起多个 Task 调用：
- Task 1: 翻译 batch_001-003
- Task 2: 翻译 batch_004-006
- Task 3: 翻译 batch_007-009
- Task 4: 翻译 batch_010-012
- Task 5: 翻译 batch_013-015
...（同时启动 3-5 个）
```

#### 子代理任务描述模板：

```
翻译任务：将日文游戏文本翻译成中文

依次翻译以下3个批次，并验证每个批次：

1. 读取 batch_XXX.json → 翻译 → 保存 translated_XXX.json → 验证
2. 读取 batch_YYY.json → 翻译 → 保存 translated_YYY.json → 验证
3. 读取 batch_ZZZ.json → 翻译 → 保存 translated_ZZZ.json → 验证

文件路径：<trans_dir>/batches/ 和 <trans_dir>/translated/

翻译规则：
- 保持 JSON 格式
- 键（key）保持不变
- 只翻译值（value）部分
- 保持游戏文本风格
- 保留特殊符号（※、★等）
- 保留变量占位符（%1、%s、{0}等）

验证命令（每翻译完一个批次后执行）：
python <skill目录>/verify_translations.py <trans_dir>/batches/batch_XXX.json <trans_dir>/translated/translated_XXX.json

如果验证发现遗漏，立即补充翻译并重新验证。
```

### 步骤 4：验证完整性

```bash
python <skill目录>/verify_translations.py <游戏文件路径>
```

脚本对比 `batches/` 和 `translated/`，找出遗漏内容保存到 `missing/`

### 步骤 5：补充遗漏（如有）

读取 `missing/` 目录中的遗漏文件，大模型亲自翻译补充后放入 `translated/`

### 步骤 6：合并翻译结果

```bash
python <skill目录>/merge_translations.py <游戏文件路径>
```

生成最终的翻译文件

## 脚本使用说明

所有脚本都支持传入游戏文件路径作为参数：

```bash
# 提取日文
python .trae/skills/game-text-translator/extract_japanese.py "path/to/game.json"

# 分批
python .trae/skills/game-text-translator/split_batches.py "path/to/game.json"

# 验证
python .trae/skills/game-text-translator/verify_translations.py "path/to/game.json"

# 合并
python .trae/skills/game-text-translator/merge_translations.py "path/to/game.json"
```

脚本会自动：
- 检测游戏文件所在目录
- 在合适的位置创建 `Trans/<游戏文件名>/` 目录
- 所有产物都放在该目录下

## 翻译示例

当大模型翻译时，应这样处理：

原文：
```json
{
    "メニュー禁止": "メニュー禁止",
    "※初期設定※": "※初期設定※",
    "じゃあウチ来る？": "じゃあウチ来る？"
}
```

翻译：
```json
{
    "メニュー禁止": "禁止菜单",
    "※初期設定※": "※初始设定※",
    "じゃあウチ来る？": "那你要来我家吗？"
}
```

## 注意事项

1. **禁止外部翻译**：大模型必须亲自翻译，不能调用 Google Translate、DeepL 等
2. **强制并行**：必须使用子代理并行翻译，不能串行逐个翻译
3. **自适应路径**：脚本自动处理路径，无需手动配置
4. **完整性检查**：翻译完成后必须运行验证脚本检查遗漏
