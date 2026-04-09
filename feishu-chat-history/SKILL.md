---
name: feishu-chat-history
description: |
  获取飞书群聊历史记录的 Skill。当用户需要获取飞书群聊天记录、
  导出群消息、备份聊天历史、分析群聊数据时，使用此 Skill。
  支持分页获取所有消息，自动处理时间排序，配置外置化。
---

# 飞书聊天记录获取 Skill

## 功能

获取飞书群聊的历史消息记录，支持：
- 自动分页获取所有消息
- 按时间范围筛选消息
- 导出为 JSON 格式
- 配置外置化（群ID、API凭证等）

## 配置方式

在使用前，需要准备配置文件 `feishu_config.json`：

```json
{
  "app_id": "cli_xxxxxxxxxxxxxxxx",
  "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "chat_id": "oc_xxxxxxxxxxxxxxxx"
}
```

## 使用方法

### 1. 获取所有聊天记录

```python
from scripts.feishu_client import FeishuClient
import json

# 加载配置
with open('feishu_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 创建客户端
client = FeishuClient(config['app_id'], config['app_secret'])

# 获取所有消息
messages = client.get_all_chat_messages(config['chat_id'])

# 保存到文件
with open('chat_history.json', 'w', encoding='utf-8') as f:
    json.dump(messages, f, indent=2, ensure_ascii=False)
```

### 2. 获取最新N条消息

```python
# 获取所有消息后取最后N条
messages = client.get_all_chat_messages(config['chat_id'])
latest_messages = messages[-10:]  # 最新10条
```

### 3. 按时间范围获取

```python
import time

# 获取最近24小时的消息
now = int(time.time() * 1000)
one_day_ago = now - 24 * 60 * 60 * 1000

all_messages = client.get_all_chat_messages(config['chat_id'])
recent_messages = [
    m for m in all_messages
    if int(m['create_time']) >= one_day_ago
]
```

## API 说明

### FeishuClient 类

#### `__init__(app_id, app_secret)`
初始化客户端
- `app_id`: 飞书应用 ID
- `app_secret`: 飞书应用密钥

#### `get_chat_messages(chat_id, page_size=50, page_token=None)`
获取消息列表（单页）
- `chat_id`: 群聊 ID
- `page_size`: 每页消息数（默认50）
- `page_token`: 分页令牌
- 返回: API 响应字典

#### `get_all_chat_messages(chat_id, page_size=50)`
获取所有消息（自动分页）
- `chat_id`: 群聊 ID
- `page_size`: 每页消息数
- 返回: 消息列表（按时间正序排列）

#### `get_chat_info(chat_id)`
获取群聊信息
- `chat_id`: 群聊 ID
- 返回: 群信息字典

## 消息格式

每条消息包含以下字段：

```json
{
  "message_id": "消息唯一ID",
  "msg_type": "消息类型(text/post/system等)",
  "create_time": "创建时间戳(毫秒)",
  "update_time": "更新时间戳(毫秒)",
  "deleted": false,
  "updated": false,
  "chat_id": "群ID",
  "sender": {
    "id": "发送者ID",
    "id_type": "ID类型(open_id/app_id等)",
    "sender_type": "发送者类型(user/app)",
    "tenant_key": "租户标识"
  },
  "body": {
    "content": "消息内容(JSON字符串)"
  },
  "mentions": [
    {
      "key": "@提及标识",
      "id": "被提及者ID",
      "id_type": "ID类型",
      "name": "被提及者名称"
    }
  ],
  "root_id": "根消息ID(回复消息时)",
  "parent_id": "父消息ID(回复消息时)"
}
```

### 消息类型说明

- **`msg_type`**: 消息类型
  - `text`: 纯文本消息（用户发送）
  - `post`: 富文本/卡片消息（机器人发送）
  - `interactive`: 交互式卡片消息（机器人发送）
  - `system`: 系统消息（如入群通知）
  - `image`: 图片消息

- **`sender.sender_type`**: 发送者类型
  - `user`: 用户发送的消息
  - `app`: 机器人/应用发送的消息
  - 空字符串: 系统消息

### ⚠️ 重要：如何正确解析所有消息

很多消息解析失败是因为没有正确处理 `msg_type`。以下是正确的解析方法：

```python
from scripts.feishu_client import FeishuClient, format_timestamp
import json
import time

client = FeishuClient(app_id, app_secret)
messages = client.get_all_chat_messages(chat_id)

def parse_message(msg):
    """
    正确解析所有类型的消息内容
    """
    msg_type = msg.get('msg_type', '')
    sender = msg.get('sender', {})
    sender_type = sender.get('sender_type', '')
    
    body = msg.get('body', {})
    content_str = body.get('content', '')
    
    # 解析消息内容
    text = ''
    try:
        content_json = json.loads(content_str)
        
        if msg_type == 'text':
            # 纯文本消息
            text = content_json.get('text', '')
        elif msg_type == 'post':
            # 富文本消息 - 提取所有 text 标签内容
            elements = content_json.get('content', [])
            parts = []
            for elem in elements:
                if isinstance(elem, list):
                    for item in elem:
                        if isinstance(item, dict) and item.get('tag') == 'text':
                            parts.append(item.get('text', ''))
            text = ''.join(parts)
        elif msg_type == 'interactive':
            # 交互式卡片 - 提取 elements 中的 text
            elements = content_json.get('elements', [])
            parts = []
            for elem in elements:
                if isinstance(elem, dict):
                    if elem.get('tag') == 'text':
                        parts.append(elem.get('text', ''))
            text = ''.join(parts)
        elif msg_type == 'image':
            text = '[图片消息]'
        else:
            text = str(content_json)[:100]
    except json.JSONDecodeError:
        text = content_str[:100]
    except Exception as e:
        text = f'[解析错误: {e}]'
    
    return {
        'msg_type': msg_type,
        'sender_type': sender_type,
        'content': text,
        'create_time': int(msg.get('create_time', 0))
    }

# 处理示例：获取机器人消息
print('=== 机器人消息 ===')
bot_count = 0
for msg in messages:
    parsed = parse_message(msg)
    if parsed['sender_type'] == 'app':
        bot_count += 1
        dt = format_timestamp(parsed['create_time'])
        print(f'[{dt}] [{parsed["msg_type"]}] {parsed["content"]}')
```

### 按发送者类型过滤

```python
# 获取所有用户消息
user_messages = [m for m in messages if m.get('sender', {}).get('sender_type') == 'user']

# 获取所有机器人消息
app_messages = [m for m in messages if m.get('sender', {}).get('sender_type') == 'app']

# 获取系统消息
system_messages = [m for m in messages if m.get('sender', {}).get('sender_type') == '']
```

### 按消息类型过滤

```python
# 获取所有文本消息
text_messages = [m for m in messages if m.get('msg_type') == 'text']

# 获取所有机器人发送的富文本消息
post_messages = [m for m in messages if m.get('msg_type') == 'post']

# 获取所有图片消息
image_messages = [m for m in messages if m.get('msg_type') == 'image']
```

### 按时间范围过滤

```python
import time

# 获取今天的消息
today_start = int(time.time() * 1000) - (int(time.time()) % (24*60*60)) * 1000

today_messages = [m for m in messages if int(m['create_time']) >= today_start]

# 获取指定时间范围
start_ts = int(time.time() * 1000) - 3600000  # 最近1小时
recent_messages = [m for m in messages if int(m['create_time']) >= start_ts]
```

### 完整示例：获取今天机器人的所有文字消息

```python
from scripts.feishu_client import FeishuClient, format_timestamp
import json
import time

client = FeishuClient(app_id, app_secret)
messages = client.get_all_chat_messages(chat_id)

# 获取今天的消息
today_start = int(time.time() * 1000) - (int(time.time()) % (24*60*60)) * 1000

# 过滤：今天 + 机器人发送
bot_messages = [
    m for m in messages 
    if int(m['create_time']) >= today_start 
    and m.get('sender', {}).get('sender_type') == 'app'
]

print(f'今天机器人共发送 {len(bot_messages)} 条消息:\n')

for msg in bot_messages:
    parsed = parse_message(msg)
    dt = format_timestamp(parsed['create_time'])
    print(f'[{dt}] {parsed["content"]}')
```

## 注意事项

1. **消息排序**: API 返回的消息按时间正序排列（旧消息在前），最新消息在最后一页
2. **分页处理**: `get_all_chat_messages` 会自动处理所有分页
3. **Token 缓存**: 客户端会自动缓存 access_token，避免频繁请求
4. **错误处理**: 所有 API 调用会抛出 `FeishuAPIError` 异常

## 依赖

- Python 3.7+
- 标准库: `urllib.request`, `json`, `time`
