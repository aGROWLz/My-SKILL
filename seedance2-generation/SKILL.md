---
name: "seedance-video"
description: "Seedance 2.0 视频生成 CLI 工具。当用户需要使用 Seedance 2.0 API 生成视频时调用，支持图片和音频参考。"
---

# Seedance 视频生成器

使用火山引擎 Seedance 2.0 API 生成视频的命令行工具。

## 功能特性

- 支持最多 9 张参考图片
- 支持最多 3 个参考音频文件
- 支持最多 3 个参考视频文件（自动上传到云端）
- 可配置分辨率 (480p, 720p)
- 可配置时长 (4-15 秒)
- 可配置宽高比 (16:9, 9:16, 1:1, 4:3, 3:4, 21:9)
- 自动轮询任务状态（每 3 秒）
- 首次运行配置向导
- 视频保存到 `seedance2-generation/output/` 目录

## 安装

1. 安装依赖：
```bash
pip install 'volcengine-python-sdk[ark]' opencv-python numpy
```

2. 首次运行时配置 API Key，或直接编辑 `scripts/config.ini`：
```ini
[API]
ARK_API_KEY = 你的API密钥

[Settings]
RESOLUTION = 720p
DURATION = 11
MODEL = seedance-2-0-fast

[R2]
WORKER_URL = https://your-worker.yourdomain.com
API_KEY = your-api-key
```

## 使用方法

```bash
cd seedance2-generation/scripts
python seedance_cli.py [选项]
```

### 命令行选项

- `-p, --prompt`: 视频生成提示词（必需）
- `-i, --images`: 图片文件路径（最多 9 个，空格分隔）
- `-a, --audio`: 音频文件路径（最多 3 个，空格分隔）
- `-v, --videos`: 视频文件路径（最多 3 个，空格分隔，自动上传）
- `-r, --resolution`: 视频分辨率 (480p/720p，默认使用配置值)
- `-d, --duration`: 视频时长秒数 (4-15，默认使用配置值)
- `--ratio`: 宽高比 (16:9/9:16/1:1/4:3/3:4/21:9，默认: 16:9)
- `--generate-audio`: 生成音频（标志，默认: True）
- `--no-generate-audio`: 禁用音频生成
- `--model`: 使用模型 (seedance-2-0/seedance-2-0-fast，默认使用配置值)
- `-o, --output`: 自定义输出目录（默认: seedance2-generation/output/）
- `--setup`: 运行配置向导

### 提示词中的资源引用标记

在提示词中可以使用 `@图像N`、`@音频N`、`@视频N` 标记来引用输入的资源，方便后续 AI 理解资源对应关系：

- `@图像1` - 引用第 1 张图片（`-i` 参数的第 1 个文件）
- `@图像2` - 引用第 2 张图片（`-i` 参数的第 2 个文件）
- `@图像9` - 引用第 9 张图片（`-i` 参数的第 9 个文件）
- `@音频1` - 引用第 1 个音频（`-a` 参数的第 1 个文件）
- `@音频2` - 引用第 2 个音频（`-a` 参数的第 2 个文件）
- `@音频3` - 引用第 3 个音频（`-a` 参数的第 3 个文件）
- `@视频1` - 引用第 1 个视频（`-v` 参数的第 1 个文件）
- `@视频2` - 引用第 2 个视频（`-v` 参数的第 2 个文件）
- `@视频3` - 引用第 3 个视频（`-v` 参数的第 3 个文件）

**重要**: 命令行中 `-i` 参数的图片按顺序对应 `@图像1` 到 `@图像9`，`-a` 参数的音频按顺序对应 `@音频1` 到 `@音频3`，`-v` 参数的视频按顺序对应 `@视频1` 到 `@视频3`。图片在前，音频在后，视频最后。

**引用方式 1 - 前置描述**：
```
根据 @图像1 中的人物形象，让 @图像1 的人物坐到 @图像2 的沙发上。声音参照 @音频1 的风格。
```

**引用方式 2 - 后置标记**（更简洁）：
```
穿红裙的女孩@图像1 拿起青苹果@图像2，放到木桌上@图像3
```

两种写法都可以，`@图像N` 标记可以放在描述的前面或后面，根据语义选择最自然的方式。

### 提示词编写规范

**必须使用具体事物名称，禁止使用代称！**

❌ **禁止使用**（代称）：
- 人称代词："他"、"她"、"ta"、"其"、"他们"
- 指示代词："这"、"那"、"这个"、"那个"
- 物主代词："它的"、"他的"、"她的"
- 模糊指代："前者"、"后者"、"上述"

✅ **必须使用**（具体名称）：
- 人物："女孩"、"男孩"、"老人"、"商人"、"@图像1 中的女性"
- 物体："红苹果"、"木桌"、"玻璃杯"、"@图像2 中的沙发"
- 动物："金毛犬"、"白猫"、"小鸟"
- 场景："海边"、"森林"、"城市街道"

**正确示例**：
```
让 @图像1 中的穿红裙女孩拿起 @图像2 中的青苹果，放到 @图像2 中的木桌上。
```

**后置标记正确示例**：
```
穿红裙的女孩@图像1 拿起青苹果@图像2，放到木桌上@图像3
```

**错误示例**：
```
让她拿起它，放到那上面。（使用了"她"、"它"、"那"等代称）
```

**原则**：提示词中的每个主体、客体都必须用具体名称或 `@图像N` 标记明确指出，确保 AI 能准确理解要操作的对象。

### 使用示例

```bash
# 基础使用 - 仅提示词
python seedance_cli.py -p "美丽的海边日落"

# 带图片和音频
python seedance_cli.py -p "跳舞的角色" -i img1.jpg img2.jpg -a music.mp3

# 带参考视频（视频会自动上传到云端）
python seedance_cli.py -p "延续@视频1的风格" -v reference.mp4 -i character.jpg

# 完整配置（图片+音频+视频）
python seedance_cli.py -p "产品展示" -i *.jpg -a bgm.mp3 -v ref1.mp4 ref2.mp4 -r 720p -d 10 --ratio 9:16

# 使用高质量模型
python seedance_cli.py -p "高质量视频" --model seedance-2-0

# 禁用音频生成
python seedance_cli.py -p "静音视频" --no-generate-audio

# 自定义输出目录
python seedance_cli.py -p "我的视频" -o /path/to/output
```

## 输出目录

生成的视频保存位置：
- **默认**: `seedance2-generation/output/seedance_{时间戳}.mp4`
- **自定义**: 通过 `-o` 选项指定

工具会在完成时打印完整的保存路径。

## 配置说明

### 首次运行

首次运行时会交互式询问以下配置：
- **API Key** (ARK_API_KEY) - 从 https://console.volcengine.com/ark/region:ark+cn-beijing/apikey 获取
- **默认分辨率** (480p/720p)
- **默认时长** (4-15 秒)
- **默认模型** (seedance-2-0-fast / seedance-2-0)
- **R2 Worker URL** 和 **API Key** - 用于上传参考视频（可选）

### 配置保存

**所有配置都会保存到 `scripts/config.ini` 文件中。**

### 再次运行是否会重复询问？

**不会。** 配置保存后，再次运行时会：
1. 自动读取 `config.ini` 中的配置
2. 直接使用已保存的默认值
3. **不会**再次询问用户

### 如何修改配置？

方法 1：直接编辑 `scripts/config.ini` 文件
方法 2：运行 `python seedance_cli.py --setup` 重新配置

## 视频生成流程

1. **输入验证**: 检查图片（最多 9 个）、音频（最多 3 个）和视频（最多 3 个）文件
2. **视频上传**: 将参考视频上传到 Cloudflare R2（如提供）
3. **文件处理**: 将图片/音频转换为 base64
4. **创建任务**: 发送请求到 Seedance API
5. **轮询状态**: 每 3 秒检查任务状态
6. **下载视频**: 将完成的视频保存到输出目录

## 视频上传模块

工具包含独立的视频上传模块 `video_uploader.py`，用于将本地视频上传到 Cloudflare R2。

### 独立使用视频上传

```python
from video_uploader import upload_video_to_r2

# 上传单个视频
url = upload_video_to_r2("/path/to/video.mp4")
print(f"上传成功: {url}")

# 上传多个视频
from video_uploader import upload_videos
urls = upload_videos(["video1.mp4", "video2.mp4"])
```

### 命令行上传视频

```bash
python video_uploader.py /path/to/video.mp4
```

## 默认设置

| 设置项 | 默认值 |
|---------|---------------|
| 水印 | 关闭 |
| 音频生成 | 开启 |
| 分辨率 | 720p（可配置） |
| 时长 | 11 秒（可配置） |
| 模型 | seedance-2-0-fast（可配置） |
| 宽高比 | 16:9 |
| 轮询间隔 | 3 秒 |
| 最大轮询次数 | 200 次 |

## 系统要求

- Python 3.8+
- volcengine-python-sdk[ark]
- OpenCV (cv2)
- NumPy
- requests（用于视频上传）

## 常见问题

**错误：ARK_API_KEY not found**
- 使用 `--setup` 标志运行以配置
- 或手动编辑 `scripts/config.ini`

**错误：Failed to create task**
- 检查 API 密钥是否有效
- 确认模型访问权限

**任务超时**
- 视频生成可能需要几分钟
- 工具每 3 秒轮询一次，最多 200 次（最长 10 分钟）
