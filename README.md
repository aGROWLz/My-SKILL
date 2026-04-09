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
└── seedance2-generation/
    ├── SKILL.md              # Skill 说明文档
    └── scripts/
        └── seedance_cli.py   # 视频生成 CLI 工具
```

## 使用说明

每个SKILL目录下都包含 `SKILL.md` 文件，详细说明了该技能的功能、配置方法和使用示例。

## 许可证

个人使用
