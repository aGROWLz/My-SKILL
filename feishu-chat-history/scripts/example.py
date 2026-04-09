#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用示例：获取飞书群聊天记录
"""
import json
import sys
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from feishu_client import FeishuClient, format_timestamp


def load_config(config_path: str = 'feishu_config.json') -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_messages(config_path: str = 'feishu_config.json', output_file: str = 'chat_history.json'):
    """获取所有聊天记录并保存"""
    config = load_config(config_path)

    client = FeishuClient(config['app_id'], config['app_secret'])

    print('正在获取所有消息...')
    messages = client.get_all_chat_messages(config['chat_id'])
    print(f'共获取 {len(messages)} 条消息')

    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    print(f'已保存到 {output_file}')

    return messages


def get_latest_messages(config_path: str = 'feishu_config.json', count: int = 10):
    """获取最新的 N 条消息"""
    config = load_config(config_path)
    client = FeishuClient(config['app_id'], config['app_secret'])

    print(f'正在获取最新 {count} 条消息...')
    messages = client.get_all_chat_messages(config['chat_id'])

    # 最新消息在最后
    latest = messages[-count:] if len(messages) >= count else messages

    print(f'\n最新 {len(latest)} 条消息：')
    print('-' * 70)
    for msg in latest:
        ts = int(msg['create_time'])
        msg_type = msg['msg_type']
        sender = msg.get('sender', {}).get('sender_type', 'unknown')
        print(f"{format_timestamp(ts)} [{msg_type}] {sender}")

    return latest


def get_recent_messages(hours: int = 24, config_path: str = 'feishu_config.json'):
    """获取最近 N 小时的消息"""
    config = load_config(config_path)
    client = FeishuClient(config['app_id'], config['app_secret'])

    now = int(time.time() * 1000)
    ago = now - hours * 60 * 60 * 1000

    print(f'正在获取最近 {hours} 小时的消息...')
    all_messages = client.get_all_chat_messages(config['chat_id'])

    recent = [m for m in all_messages if int(m['create_time']) >= ago]
    print(f'找到 {len(recent)} 条消息')

    return recent


def get_chat_info(config_path: str = 'feishu_config.json'):
    """获取群信息"""
    config = load_config(config_path)
    client = FeishuClient(config['app_id'], config['app_secret'])

    info = client.get_chat_info(config['chat_id'])
    return info


if __name__ == '__main__':
    # 示例用法

    # 1. 获取所有消息
    # get_all_messages()

    # 2. 获取最新10条消息
    get_latest_messages(count=10)

    # 3. 获取最近24小时的消息
    # get_recent_messages(hours=24)

    # 4. 获取群信息
    # info = get_chat_info()
    # print(json.dumps(info, indent=2, ensure_ascii=False))
