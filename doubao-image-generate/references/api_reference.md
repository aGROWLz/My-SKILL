# 豆包图像生成 API 参考

## 环境配置

### 环境变量

```bash
export ARK_API_KEY="your-api-key-here"
export ARK_IMAGE_MODEL_ID="doubao-seedream-5-0-260128"
```

### 依赖安装

```bash
pip install --upgrade "openai>=1.0"
pip install requests
```

## API 接口

### 1. 文生图 (Text-to-Image)

根据文本提示词生成图片。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 图片描述提示词 |
| size | string | 否 | 图片尺寸，默认 "2K"，可选 "4K" |
| watermark | boolean | 否 | 是否添加水印，默认 false |
| response_format | string | 否 | 返回格式，默认 "url"，可选 "b64_json" |

#### 示例代码

```python
from scripts.doubao_image_client import DoubaoImageClient

client = DoubaoImageClient()

result = client.text_to_image(
    prompt="古装帅哥，中国古代武侠风格，英俊潇洒，身穿青色长袍",
    size="2K",
    watermark=False
)

if result["success"]:
    print(f"生成成功：{result['url']}")
    print(f"类型：{result['type']}")
    print(f"预估成本：{result['cost']['estimated_cost_cny']} 元")
else:
    print(f"生成失败：{result['error']}")
```

### 2. 单图参考生图 (Image-to-Image)

根据一张参考图片生成新图片。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 图片描述提示词 |
| image_url | string | 是 | 参考图片 URL |
| size | string | 否 | 图片尺寸，默认 "2K" |
| watermark | boolean | 否 | 是否添加水印 |
| response_format | string | 否 | 返回格式 |

#### 示例代码

```python
result = client.single_image_to_image(
    prompt="将背景换成蓝色天空，保持人物不变",
    image_url="https://example.com/reference.png",
    size="2K",
    watermark=False
)

if result["success"]:
    print(f"生成成功：{result['url']}")
    print(f"参考图：{result['reference_images']}")
```

### 3. 多图参考生图 (Multi-Image-to-Image)

根据多张参考图片生成新图片。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 图片描述提示词 |
| image_urls | string[] | 是 | 参考图片 URL 列表 |
| size | string | 否 | 图片尺寸，默认 "2K" |
| watermark | boolean | 否 | 是否添加水印 |
| sequential_generation | string | 否 | 顺序图像生成，默认 "disabled" |
| response_format | string | 否 | 返回格式 |

#### 示例代码

```python
result = client.multi_image_to_image(
    prompt="将图 1 的服装换为图 2 的服装",
    image_urls=[
        "https://example.com/person.png",
        "https://example.com/clothes.png"
    ],
    size="2K",
    watermark=False,
    sequential_generation="disabled"
)

if result["success"]:
    print(f"生成成功：{result['url']}")
    print(f"参考图数量：{len(result['reference_images'])}")
```

## 成本管理

### CostTracker 类

自动跟踪和估算 API 调用成本，支持按类型统计。

```python
# 获取当前会话成本摘要
summary = client.cost_tracker.get_session_summary()
print(f"总调用次数：{summary['total_generations']}")
print(f"文生图：{summary['by_type'].get('text2image', 0)} 次")
print(f"单图参考：{summary['by_type'].get('single', 0)} 次")
print(f"多图参考：{summary['by_type'].get('multi', 0)} 次")
print(f"总预估成本：{summary['total_estimated_cost_cny']} 元")

# 重置成本跟踪
client.cost_tracker.reset()
```

### 成本估算

| 类型 | 2K 尺寸 | 4K 尺寸 | 说明 |
|------|--------|--------|------|
| 文生图 | ¥0.01 | ¥0.02 | 基础成本 |
| 单图参考 | ¥0.011 | ¥0.022 | 文生图 × 1.1 |
| 多图参考 | ¥0.0132+ | ¥0.0264+ | 单图 + ¥0.002/张 |

> 注意：以上为估算值，实际成本请参考豆包官方定价

## 错误处理

### 重试机制

客户端内置重试机制，默认重试 3 次，使用指数退避策略。

```python
# 自定义重试配置
result = client.text_to_image(
    prompt="...",
    max_retries=5,      # 最大重试次数
    retry_delay=3.0     # 初始重试延迟 (秒)
)
```

### 错误类型

#### 不重试的错误

- `invalid_api_key` - API 密钥无效
- `authentication` - 认证失败
- `permission` - 权限不足
- `invalid_prompt` - 提示词无效
- `content_policy` - 内容政策违规

#### 可重试的错误

- `timeout` - 请求超时
- `rate limit` - 速率限制
- `service unavailable` - 服务不可用
- `internal server` - 服务器内部错误
- `connection` - 连接错误

### 错误处理示例

```python
result = client.text_to_image(prompt="...")

if not result["success"]:
    print(f"生成失败：{result['error']}")
    print(f"尝试次数：{result['attempts']}")
    print(f"生成类型：{result['type']}")
```

## CLI 使用

### 文生图

```bash
python scripts/doubao_image_client.py text \
    "古装帅哥，中国古代武侠风格" \
    --size 2K
```

### 单图生图

```bash
python scripts/doubao_image_client.py single \
    "将背景换成蓝色天空" \
    "https://example.com/reference.png" \
    --size 2K
```

### 多图生图

```bash
python scripts/doubao_image_client.py multi \
    "将图 1 的服装换为图 2 的服装" \
    "https://example.com/img1.png" \
    "https://example.com/img2.png" \
    --size 2K \
    --sequential disabled
```

## 最佳实践

### 1. 提示词优化

**文生图：**
- 描述清晰具体，包含主体、背景、风格
- 使用形容词增强效果
- 避免模糊或矛盾的指令

**图生图：**
- 明确说明要保留什么、改变什么
- 多图参考时说明每张图片的作用

### 2. 成本控制

- **批量生成优先文生图** - 成本最低
- **合理选择尺寸** - 2K 足够大多数场景
- **监控成本摘要** - 定期查看 `get_session_summary()`
- **避免不必要的多图参考** - 每增加一张参考图都增加成本

### 3. 错误处理

- 实现重试逻辑（已内置）
- 记录失败请求以便分析
- 监控 API 可用性
- 区分可重试和不可重试错误

### 4. 图片质量

- 使用高质量参考图片
- 图片 URL 可公开访问
- 多图参考时确保图片相关性
- 提示词与参考图风格一致
