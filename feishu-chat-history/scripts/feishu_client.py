#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书 API 客户端模块
提供群聊消息获取、群信息查询等功能
"""
import urllib.request
import urllib.error
import json
import time


class FeishuClient:
    """飞书 API 客户端"""

    BASE_URL = 'https://open.feishu.cn/open-apis'

    def __init__(self, app_id: str, app_secret: str):
        """
        初始化客户端

        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._token_expire_time = 0

    def _get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        url = f'{self.BASE_URL}/auth/v3/tenant_access_token/internal'
        data = f'app_id={self.app_id}&app_secret={self.app_secret}'.encode()
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get('tenant_access_token')

    def get_token(self) -> str:
        """获取有效的 token（带缓存）"""
        now = time.time()
        if not self._token or now >= self._token_expire_time:
            self._token = self._get_tenant_access_token()
            # token 有效期约 2 小时，这里设置 1.5 小时后刷新
            self._token_expire_time = now + 5400
        return self._token

    def request(self, method: str, path: str, **kwargs) -> dict:
        """
        发送 API 请求

        Args:
            method: HTTP 方法 (GET, POST, etc.)
            path: API 路径（不含 BASE_URL）
            **kwargs: 额外参数
                - params: URL 查询参数 (dict)
                - data: POST 数据 (bytes 或 dict)
                - headers: 额外请求头 (dict)

        Returns:
            API 响应的 JSON 数据
        """
        url = f'{self.BASE_URL}/{path.lstrip("/")}'

        # 添加查询参数
        params = kwargs.get('params')
        if params:
            query = '&'.join(f'{k}={v}' for k, v in params.items())
            url = f'{url}?{query}'

        # 准备请求数据
        data = kwargs.get('data')
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=data, method=method)

        # 添加默认请求头
        req.add_header('Authorization', f'Bearer {self.get_token()}')
        if data:
            req.add_header('Content-Type', 'application/json; charset=utf-8')

        # 添加额外请求头
        headers = kwargs.get('headers')
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                error_json = json.loads(error_body)
                raise FeishuAPIError(f"HTTP {e.code}: {error_json}")
            except json.JSONDecodeError:
                raise FeishuAPIError(f"HTTP {e.code}: {error_body}")

    def get_chat_info(self, chat_id: str) -> dict:
        """
        获取群信息

        Args:
            chat_id: 群 ID

        Returns:
            群信息字典
        """
        return self.request('GET', f'/im/v1/chats/{chat_id}')

    def get_chat_messages(self, chat_id: str, page_size: int = 50, page_token: str = None) -> dict:
        """
        获取会话历史消息（单页）

        Args:
            chat_id: 群 ID
            page_size: 每页消息数量
            page_token: 分页 token

        Returns:
            消息列表数据
        """
        params = {
            'container_id_type': 'chat',
            'container_id': chat_id,
            'page_size': page_size
        }
        if page_token:
            params['page_token'] = page_token

        return self.request('GET', '/im/v1/messages', params=params)

    def get_all_chat_messages(self, chat_id: str, page_size: int = 50) -> list:
        """
        获取群的所有消息（自动分页）

        注意：API 返回的消息按时间正序排列（旧消息在前），
        最新消息在最后一页。本方法会获取所有分页。

        Args:
            chat_id: 群 ID
            page_size: 每页消息数量

        Returns:
            所有消息的列表（按时间正序排列）
        """
        all_messages = []
        page_token = None

        while True:
            result = self.get_chat_messages(chat_id, page_size, page_token)
            data = result.get('data', {})
            items = data.get('items', [])
            all_messages.extend(items)

            page_token = data.get('page_token')
            has_more = data.get('has_more', False)

            if not has_more or not page_token:
                break

        return all_messages

    def get_message_detail(self, message_id: str) -> dict:
        """
        获取消息详情

        Args:
            message_id: 消息 ID

        Returns:
            消息详情
        """
        return self.request('GET', f'/im/v1/messages/{message_id}')

    def get_chats(self, page_size: int = 50) -> dict:
        """
        获取机器人所在的群列表

        Args:
            page_size: 每页数量

        Returns:
            群列表数据
        """
        return self.request('GET', '/im/v1/chats', params={'page_size': page_size})

    def get_chat_members(self, chat_id: str, page_size: int = 50) -> dict:
        """
        获取群成员列表

        Args:
            chat_id: 群 ID
            page_size: 每页数量

        Returns:
            成员列表数据
        """
        return self.request('GET', f'/im/v1/chats/{chat_id}/members', params={'page_size': page_size})


class FeishuAPIError(Exception):
    """飞书 API 错误"""
    pass


def format_timestamp(ts_ms: int) -> str:
    """将毫秒时间戳格式化为可读字符串"""
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts_ms / 1000))


def parse_message_content(body_content: str, msg_type: str = '') -> str:
    """
    解析消息内容，支持所有消息类型
    
    Args:
        body_content: 消息体中的 content 字段（JSON 字符串）
        msg_type: 消息类型 (text, post, interactive, image, system 等)
    
    Returns:
        解析后的文字内容
    """
    if not body_content:
        return '(空内容)'

    try:
        content_json = json.loads(body_content)
        
        if msg_type == 'text':
            # 纯文本消息
            return content_json.get('text', '')
        elif msg_type == 'post':
            # 富文本消息 - 提取所有 text 标签内容
            elements = content_json.get('content', [])
            parts = []
            for elem in elements:
                if isinstance(elem, list):
                    for item in elem:
                        if isinstance(item, dict) and item.get('tag') == 'text':
                            parts.append(item.get('text', ''))
            return ''.join(parts)
        elif msg_type == 'interactive':
            # 交互式卡片 - 提取 elements 中的 text (elements 是二维数组)
            all_elements = content_json.get('elements', [])
            parts = []
            has_image = False
            for outer in all_elements:
                if isinstance(outer, list):
                    for elem in outer:
                        if isinstance(elem, dict):
                            if elem.get('tag') == 'text':
                                text = elem.get('text', '')
                                if text:  # 只添加非空文本
                                    parts.append(text)
                            elif elem.get('tag') == 'img':
                                has_image = True
            if parts:
                return ''.join(parts)
            elif has_image:
                return '[图片消息]'
            return '[交互卡片消息]'
        elif msg_type == 'image':
            return '[图片消息]'
        elif msg_type == 'system':
            return content_json.get('template', str(content_json))
        else:
            return str(content_json)[:200]
    except json.JSONDecodeError:
        return body_content[:200]
    except Exception as e:
        return f'[解析错误: {e}]'
