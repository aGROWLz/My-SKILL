# My-SKILL

我的个人SKILL集合 - 存储我自己编写的各种技能

## 仓库简介

这个仓库用于存储和管理我自己编写的各种SKILL（技能），主要用于AI助手场景下的功能扩展。

## SKILL 列表

### 1. feishu-chat-history

**功能描述**: 获取飞书群聊历史记录的 Skill。

**适用场景**:
- 获取飞书群聊天记录
- 导出群消息
- 备份聊天历史
- 分析群聊数据

**主要特性**:
- 自动分页获取所有消息
- 按时间范围筛选消息
- 导出为 JSON 格式
- 配置外置化（群ID、API凭证等）

**技术栈**: Python 3.7+

### 2. seedance2-generation

**功能描述**: Seedance 2.0 视频生成 CLI 工具。

**适用场景**:
- 使用 Seedance 2.0 API 生成视频
- 支持图片和音频参考

**主要特性**:
- 支持最多 9 张参考图片
- 支持最多 3 个参考音频文件
- 支持最多 3 个参考视频文件
- 可配置分辨率 (480p, 720p)
- 可配置时长 (4-15 秒)
- 自动轮询任务状态

**技术栈**: Python 3.8+

### 3. doubao-image-generate

**功能描述**: 豆包图像生成 API 集成，支持文生图/单图参考/多图参考。

**适用场景**:
- 生成图片（文生图）
- 修改图片（图生图）
- 换背景
- 风格转换
- 图像融合

**主要特性**:
- 自动识别用户意图（纯文本→文生图，带图片→图生图）
- 成本精细化管理
- 错误处理与重试机制
- 图片自动下载到本地
- 支持飞书发送

**技术栈**: Python 3.7+

### 4. script-analysis

**功能描述**: 短剧剧本分析与生成助手，完成从需求理解到完整剧本的全流程工作。

**适用场景**:
- 短剧改编与创作
- 剧本需求分析
- 故事骨架搭建
- 分集规划与付费卡点设计
- 逐集剧本编写

**主要特性**:
- 三阶段完整工作流程（项目初始化→故事骨架→改编策略→剧本编写）
- 付费卡点设计（按10%/30%/50%/70%/90%分布）
- 多类型节奏框架支持（甜宠/虐恋/萌宝/战神/重生等）
- 质量审核标准（故事骨架/改编策略/剧本三个维度）
- 竖屏短剧专用规范

**技术栈**: Python 3.7+

## 目录结构

```
My-SKILL/
├── README.md
├── .gitignore
├── feishu-chat-history/
│   ├── SKILL.md              # Skill 说明文档
│   ├── feishu_config.example.json  # 配置文件示例
│   └── scripts/
│       ├── feishu_client.py  # 飞书客户端核心代码
│       └── example.py        # 使用示例
├── seedance2-generation/
│   ├── SKILL.md              # Skill 说明文档
│   └── scripts/
│       ├── seedance_cli.py   # 视频生成 CLI 工具
│       ├── video_uploader.py # 视频上传工具
│       └── config.ini.example # 配置文件示例
├── doubao-image-generate/
│   ├── SKILL.md              # Skill 说明文档
│   ├── .env.example          # 环境变量配置示例
│   ├── .gitignore            # Git 忽略文件
│   ├── references/
│   │   └── api_reference.md  # API 参考文档
│   └── scripts/
│       └── doubao_image_client.py # 豆包图像生成客户端
└── script-analysis/
    └── SKILL.md              # Skill 说明文档
```

## 安装方法

### 方法 1：克隆整个仓库

```bash
git clone https://github.com/aGROWLz/My-SKILL.git
```

### 方法 2：只安装单个 Skill（推荐）

如果你只需要其中一个 Skill，可以使用 `svn export` 精准下载，无需克隆整个仓库：

```bash
# 安装 feishu-chat-history
svn export https://github.com/aGROWLz/My-SKILL/trunk/feishu-chat-history

# 安装 seedance2-generation
svn export https://github.com/aGROWLz/My-SKILL/trunk/seedance2-generation

# 安装 doubao-image-generate
svn export https://github.com/aGROWLz/My-SKILL/trunk/doubao-image-generate

# 安装 script-analysis
svn export https://github.com/aGROWLz/My-SKILL/trunk/script-analysis
```

**通用格式**：
```bash
svn export https://github.com/aGROWLz/My-SKILL/trunk/<skill-name>
```

## 使用说明

每个SKILL目录下都包含 `SKILL.md` 文件，详细说明了该技能的功能、配置方法和使用示例。

## 许可证

个人使用
