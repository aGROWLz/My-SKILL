---
name: doubao-image-generate
description: 豆包图像生成 API 集成，支持文生图/单图参考/多图参考，包含成本精细化管理和错误处理与重试机制。自动识别用户意图：纯文本请求→文生图，带图片请求→图生图（用户图片保存在 /root/.openclaw/media/inbound/）。图片自动下载到本地并可通过飞书发送。使用当需要：(1) 生成图片，(2) 修改图片，(3) 换背景，(4) 风格转换，(5) 图像融合
---

# 豆包图像生成技能

基于火山引擎豆包 Seedream 模型的图像生成能力，**自动识别用户意图**：
- **纯文本请求** → 文生图
- **带图片请求** → 图生图（用户图片在 `/root/.openclaw/media/inbound/`）
- **图片自动下载** → 保存到本地并可通过飞书发送

## 🚀 快速开始 - 自然语言指令

### 文生图 (纯文本)

**你只需要说：**
```
"帮我生成一张古装帅哥图片"
"生成一张夕阳海滩的风景照"
"画一只可爱的猫咪"
```

**我会：**
1. 自动调用 `text_to_image()`
2. 下载图片到本地
3. 通过飞书发送给你

### 图生图 (带图片)

**你只需要说：**
```
[发送图片] "把这张图片的背景换成蓝色"
[发送图片] "把这个人的衣服换成红色"
[发送图片] "改成赛博朋克风格"
```

**我会：**
1. 识别图片路径：`/root/.openclaw/media/inbound/[message_id].png`
2. 自动调用 `single_image_to_image()`
3. 下载生成的图片到本地
4. 通过飞书发送给你

### 多图融合

**你只需要说：**
```
[发送图片 1] [发送图片 2] "把图 1 的人穿上图 2 的衣服"
[发送图片 1] [发送图片 2] "融合这两张图"
```

**我会：**
1. 识别图片路径：`/root/.openclaw/media/inbound/[message_id_1].png` 和 `[message_id_2].png`
2. 自动调用 `multi_image_to_image()`
3. 下载生成的图片到本地
4. 通过飞书发送给你

## 配置环境变量

```bash
export ARK_API_KEY="your-api-key-here"
export ARK_IMAGE_MODEL_ID="doubao-seedream-5-0-260128"
```

## 核心功能

### 1. 智能意图识别

**纯文本 → 文生图**
```
你说："请你帮我生成一张古装帅哥图片"
↓ 自动识别为文生图
调用：client.text_to_image(prompt="古装帅哥", size="2K")
```

**带图片 → 图生图**
```
你说：[图片] "把这张图片的背景换成蓝色"
↓ 自动识别图片路径
图片路径：/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg
↓ 自动识别为单图参考生图
调用：client.single_image_to_image(
    prompt="将背景换成蓝色",
    image_url="/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg",
    size="2K"
)
```

**多图 → 多图融合**
```
你说：[图片 1] [图片 2] "把图 1 的人穿上图 2 的衣服"
↓ 自动识别图片路径
图片 1: /root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg
图片 2: /root/.openclaw/media/inbound/2374463c-128a-51bc-bd14-890cd9b73cd8.jpg
↓ 自动识别为多图参考生图
调用：client.multi_image_to_image(
    prompt="将图 1 的人物穿上图 2 的服装",
    image_urls=[
        "/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg",
        "/root/.openclaw/media/inbound/2374463c-128a-51bc-bd14-890cd9b73cd8.jpg"
    ],
    size="2K"
)
```

### 2. 用户图片路径识别

**飞书图片保存规则：**
- 用户发送的图片会自动保存到：`/root/.openclaw/media/inbound/`
- 文件名格式：`[UUID].[扩展名]` (如：`1263352b-0179-40ab-ac03-789bc8a62bc7.jpg`)
- 示例：`/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg`

**识别流程：**
```python
# 1. 从消息元数据获取图片路径
image_path = "/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg"

# 2. 验证文件存在
if os.path.exists(image_path):
    # 3. 调用图生图
    result = client.single_image_to_image(
        prompt="用户指令",
        image_url=image_path,  # 使用本地路径
        size="2K"
    )
```

### 3. 图片自动下载

生成的图片会自动下载到本地：
```
skills/doubao-image-to-image/doubao-image-to-image/generated_images/
├── generated_20260326_111122_a1b2c3d4.jpg
├── generated_20260326_111233_e5f6g7h8.jpg
└── ...
```

### 4. 飞书发送

生成图片后，我会通过飞书发送给你：
```python
# 生成图片
result = client.single_image_to_image(
    prompt="换背景",
    image_url="/root/.openclaw/media/inbound/om_xxxxx.png"
)

# 获取本地路径
local_path = result['local_path']  # /path/to/generated_20260326_....jpg

# 通过飞书发送
message.send(
    channel="feishu",
    path=local_path,
    caption=f"✅ 图片生成成功！\n💰 成本：¥{result['cost']['estimated_cost_cny']}"
)
```

## Python 代码调用

### 1. 文生图

```python
from scripts.doubao_image_client import DoubaoImageClient

client = DoubaoImageClient()

result = client.text_to_image(
    prompt="古装帅哥，中国古代武侠风格，英俊潇洒",
    size="2K",
    save_locally=True  # 默认 True，自动下载
)

if result["success"]:
    print(f"✅ 生成成功")
    print(f"📁 本地路径：{result['local_path']}")
    print(f"💰 成本：{result['cost']['estimated_cost_cny']} 元")
```

### 2. 单图参考生图 (使用用户图片)

```python
# 用户发送的图片路径
user_image_path = "/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg"

result = client.single_image_to_image(
    prompt="将背景换成蓝色天空",
    image_url=user_image_path,  # 使用本地路径
    size="2K",
    save_locally=True
)

if result["success"]:
    print(f"图片已保存至：{result['local_path']}")
```

### 3. 多图参考生图 (使用用户图片)

```python
# 用户发送的多张图片路径
user_images = [
    "/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg",
    "/root/.openclaw/media/inbound/2374463c-128a-51bc-bd14-890cd9b73cd8.jpg"
]

result = client.multi_image_to_image(
    prompt="将图 1 的服装换为图 2 的服装",
    image_urls=user_images,  # 使用本地路径列表
    size="2K",
    save_locally=True
)
```

## 成本管理

### 自动成本跟踪

```python
# 获取成本摘要
summary = client.cost_tracker.get_session_summary()
print(f"总调用：{summary['total_generations']} 次")
print(f"文生图：{summary['by_type'].get('text2image', 0)} 次")
print(f"单图参考：{summary['by_type'].get('single', 0)} 次")
print(f"多图参考：{summary['by_type'].get('multi', 0)} 次")
print(f"总成本：{summary['total_estimated_cost_cny']} 元")
```

### 成本对比

| 类型 | 2K 尺寸 | 4K 尺寸 | 说明 |
|------|--------|--------|------|
| 文生图 | ¥0.01 | ¥0.02 | 最便宜 |
| 单图参考 | ¥0.011 | ¥0.022 | +10% |
| 多图参考 | ¥0.0132+ | ¥0.0264+ | +32%/张 |

## 错误处理与重试

- **自动重试**：默认 3 次，指数退避
- **智能判断**：区分可重试/不可重试错误
- **详细日志**：记录每次尝试

## CLI 工具

```bash
# 文生图 (自动下载)
python scripts/doubao_image_client.py text "古装帅哥，武侠风格" --size 2K

# 单图生图 (自动下载)
python scripts/doubao_image_client.py single "换背景" "图片 URL 或本地路径" --size 2K

# 多图生图 (自动下载)
python scripts/doubao_image_client.py multi "融合" "URL1 或路径 1" "URL2 或路径 2" --size 2K

# 不下载 (只返回 URL)
python scripts/doubao_image_client.py text "古装帅哥" --no-save
```

## 完整工作流程示例

### 示例 1: 文生图 + 飞书发送

**用户输入：**
```
请你帮我生成一张古装帅哥图片
```

**自动处理流程：**
```python
# 1. 识别意图：文生图
# 2. 调用 API
result = client.text_to_image(
    prompt="古装帅哥，中国古代武侠风格，英俊潇洒...",
    size="2K",
    save_locally=True
)

# 3. 图片已下载到本地
local_path = result['local_path']

# 4. 通过飞书发送
message.send(
    channel="feishu",
    path=local_path,
    caption=f"✅ 图片生成成功！\n💰 成本：¥{result['cost']['estimated_cost_cny']}"
)
```

### 示例 2: 图生图 + 飞书发送

**用户输入：**
```
[图片：1263352b-0179-40ab-ac03-789bc8a62bc7.jpg]
请你帮我把这张图片的背景换成蓝色
```

**自动处理流程：**
```python
# 1. 识别意图：单图参考生图
# 2. 获取用户图片路径
user_image_path = "/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg"

# 3. 验证文件存在
if os.path.exists(user_image_path):
    # 4. 调用 API
    result = client.single_image_to_image(
        prompt="将背景换成蓝色天空，保持人物不变",
        image_url=user_image_path,
        size="2K",
        save_locally=True
    )
    
    # 5. 图片已下载到本地
    local_path = result['local_path']
    
    # 6. 通过飞书发送
    message.send(
        channel="feishu",
        path=local_path,
        caption=f"✅ 背景已更换！\n💰 成本：¥{result['cost']['estimated_cost_cny']}"
    )
else:
    print(f"❌ 图片文件不存在：{user_image_path}")
```

### 示例 3: 多图融合 + 飞书发送

**用户输入：**
```
[图片 1: 1263352b-0179-40ab-ac03-789bc8a62bc7.jpg] 
[图片 2: 2374463c-128a-51bc-bd14-890cd9b73cd8.jpg]
把图 1 的人穿上图 2 的衣服
```

**自动处理流程：**
```python
# 1. 识别意图：多图参考生图
# 2. 获取用户图片路径
user_images = [
    "/root/.openclaw/media/inbound/1263352b-0179-40ab-ac03-789bc8a62bc7.jpg",
    "/root/.openclaw/media/inbound/2374463c-128a-51bc-bd14-890cd9b73cd8.jpg"
]

# 3. 验证所有文件存在
all_exist = all(os.path.exists(p) for p in user_images)

if all_exist:
    # 4. 调用 API
    result = client.multi_image_to_image(
        prompt="将图 1 的人物穿上图 2 的服装",
        image_urls=user_images,
        size="2K",
        save_locally=True
    )
    
    # 5. 图片已下载到本地
    local_path = result['local_path']
    
    # 6. 通过飞书发送
    message.send(
        channel="feishu",
        path=local_path,
        caption=f"✅ 图片融合成功！\n💰 成本：¥{result['cost']['estimated_cost_cny']}"
    )
```

## 注意事项

1. **文生图** - 只需描述想要的内容
2. **单图参考** - 发送 1 张图 + 说明修改需求
3. **多图参考** - 发送 2+ 张图 + 说明融合方式
4. **用户图片路径** - `/root/.openclaw/media/inbound/[UUID].[扩展名]` (如：`1263352b-0179-40ab-ac03-789bc8a62bc7.jpg`)
5. **生成图片路径** - `generated_images/generated_[timestamp]_[uuid].jpg`
6. **图片自动下载** - 默认保存到 `generated_images/` 目录
7. **飞书发送** - 生成后自动通过飞书发送
8. **定期查看成本摘要控制预算**

## 详细文档

完整 API 文档见 [references/api_reference.md](references/api_reference.md)
