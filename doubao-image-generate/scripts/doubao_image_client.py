#!/usr/bin/env python3
"""
豆包图像生成 API 客户端 - 支持文生图/单图参考/多图参考
包含成本管理和重试机制，支持飞书发送图片
"""

import os
import time
import json
import hashlib
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from openai import OpenAI
import requests


class DoubaoImageClient:
    """豆包图像生成 API 客户端 (文生图 + 图生图)"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化客户端
        
        Args:
            api_key: 豆包 API 密钥 (优先从环境变量 ARK_API_KEY 读取)
            base_url: API 基础 URL
        """
        self.api_key = api_key or os.getenv('ARK_API_KEY')
        if not self.api_key:
            raise ValueError("ARK_API_KEY 环境变量未设置")
        
        self.base_url = base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self.model = os.getenv('ARK_IMAGE_MODEL_ID', 'doubao-seedream-5-0-260128')
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # 成本管理
        self.cost_tracker = CostTracker()
        
        # 图片保存目录
        self.image_dir = os.path.join(os.path.dirname(__file__), '..', 'generated_images')
        os.makedirs(self.image_dir, exist_ok=True)
    
    def text_to_image(
        self,
        prompt: str,
        size: str = "2K",
        watermark: bool = False,
        response_format: str = "url",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        save_locally: bool = True
    ) -> Dict[str, Any]:
        """
        文生图 - 根据文本提示词生成图片
        
        Args:
            prompt: 图片描述提示词
            size: 图片尺寸 (2K, 4K 等)
            watermark: 是否添加水印
            response_format: 返回格式 (url 或 b64_json)
            max_retries: 最大重试次数
            retry_delay: 重试延迟 (秒)
            save_locally: 是否保存到本地
            
        Returns:
            包含结果和成本信息的字典
        """
        return self._generate_with_retry(
            prompt=prompt,
            image_urls=None,
            size=size,
            watermark=watermark,
            response_format=response_format,
            max_retries=max_retries,
            retry_delay=retry_delay,
            is_text_to_image=True,
            save_locally=save_locally
        )
    
    def _convert_local_to_base64(self, local_path: str) -> str:
        """
        将本地图片转换为 base64 数据 URI
        
        Args:
            local_path: 本地图片路径
            
        Returns:
            base64 数据 URI
        """
        import base64
        
        # 获取文件扩展名
        ext = os.path.splitext(local_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')
        
        with open(local_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        return f"data:{mime_type};base64,{img_data}"
    
    def single_image_to_image(
        self,
        prompt: str,
        image_url: str,
        size: str = "2K",
        watermark: bool = False,
        response_format: str = "url",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        save_locally: bool = True
    ) -> Dict[str, Any]:
        """
        单图参考生图
        
        Args:
            prompt: 图片描述提示词
            image_url: 参考图片 URL 或本地路径
            size: 图片尺寸 (2K, 4K 等)
            watermark: 是否添加水印
            response_format: 返回格式 (url 或 b64_json)
            max_retries: 最大重试次数
            retry_delay: 重试延迟 (秒)
            save_locally: 是否保存到本地
            
        Returns:
            包含结果和成本信息的字典
        """
        # 如果是本地路径，转换为 base64
        image_urls = [image_url]
        if os.path.exists(image_url):
            image_urls = [self._convert_local_to_base64(image_url)]
        
        return self._generate_with_retry(
            prompt=prompt,
            image_urls=image_urls,
            size=size,
            watermark=watermark,
            response_format=response_format,
            max_retries=max_retries,
            retry_delay=retry_delay,
            is_multi_reference=False,
            save_locally=save_locally
        )
    
    def multi_image_to_image(
        self,
        prompt: str,
        image_urls: List[str],
        size: str = "2K",
        watermark: bool = False,
        response_format: str = "url",
        sequential_generation: str = "disabled",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        save_locally: bool = True
    ) -> Dict[str, Any]:
        """
        多图参考生图
        
        Args:
            prompt: 图片描述提示词
            image_urls: 参考图片 URL 列表 (支持本地路径)
            size: 图片尺寸 (2K, 4K 等)
            watermark: 是否添加水印
            response_format: 返回格式 (url 或 b64_json)
            sequential_generation: 顺序图像生成 ("disabled" 或 "enabled")
            max_retries: 最大重试次数
            retry_delay: 重试延迟 (秒)
            save_locally: 是否保存到本地
            
        Returns:
            包含结果和成本信息的字典
        """
        if not image_urls or len(image_urls) == 0:
            raise ValueError("参考图片 URL 列表不能为空")
        
        # 转换本地路径为 base64
        converted_urls = []
        for url in image_urls:
            if os.path.exists(url):
                converted_urls.append(self._convert_local_to_base64(url))
            else:
                converted_urls.append(url)
        
        return self._generate_with_retry(
            prompt=prompt,
            image_urls=converted_urls,
            size=size,
            watermark=watermark,
            response_format=response_format,
            max_retries=max_retries,
            retry_delay=retry_delay,
            is_multi_reference=True,
            sequential_generation=sequential_generation,
            save_locally=save_locally
        )
    
    def _generate_with_retry(
        self,
        prompt: str,
        image_urls: Optional[List[str]],
        size: str,
        watermark: bool,
        response_format: str,
        max_retries: int,
        retry_delay: float,
        is_text_to_image: bool = False,
        is_multi_reference: bool = False,
        sequential_generation: str = "disabled",
        save_locally: bool = True
    ) -> Dict[str, Any]:
        """
        带重试机制的图像生成
        
        Args:
            prompt: 提示词
            image_urls: 参考图片 URL 列表 (文生图为 None)
            size: 图片尺寸
            watermark: 是否添加水印
            response_format: 返回格式
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            is_text_to_image: 是否为文生图
            is_multi_reference: 是否为多图参考
            sequential_generation: 顺序图像生成设置
            save_locally: 是否保存到本地
            
        Returns:
            包含结果和成本信息的字典
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"生成尝试 {attempt + 1}/{max_retries}...")
                
                # 构建 extra_body
                extra_body = {
                    "watermark": watermark,
                }
                
                if is_text_to_image:
                    # 文生图：不传 image 参数
                    pass
                elif is_multi_reference:
                    # 多图参考
                    extra_body["image"] = image_urls
                    extra_body["sequential_image_generation"] = sequential_generation
                else:
                    # 单图参考
                    extra_body["image"] = image_urls[0]
                
                # 调用 API
                response = self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    size=size,
                    response_format=response_format,
                    extra_body=extra_body,
                )
                
                # 检查响应
                if not response.data or len(response.data) == 0:
                    raise Exception("API 返回空数据")
                
                result_url = response.data[0].url
                
                # 下载并保存图片
                local_path = None
                if save_locally:
                    local_path = self._download_image(result_url)
                    print(f"图片已保存至：{local_path}")
                
                # 记录成本
                ref_count = 0 if is_text_to_image else len(image_urls)
                cost_info = self.cost_tracker.record_generation(
                    model=self.model,
                    size=size,
                    image_count=ref_count,
                    generation_type="text2image" if is_text_to_image else ("multi" if is_multi_reference else "single")
                )
                
                result = {
                    "success": True,
                    "url": result_url,
                    "local_path": local_path,
                    "prompt": prompt,
                    "size": size,
                    "cost": cost_info,
                    "attempts": attempt + 1,
                    "timestamp": datetime.now().isoformat(),
                    "type": "text2image" if is_text_to_image else ("multi_image2image" if is_multi_reference else "image2image")
                }
                
                if not is_text_to_image:
                    result["reference_images"] = image_urls
                
                return result
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # 判断是否需要重试
                should_retry = self._should_retry(error_msg, attempt, max_retries)
                
                if should_retry and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    print(f"  失败：{error_msg}")
                    print(f"  {wait_time:.1f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"  失败：{error_msg}")
        
        # 所有重试都失败
        return {
            "success": False,
            "error": str(last_error),
            "attempts": max_retries,
            "timestamp": datetime.now().isoformat(),
            "type": "text2image" if is_text_to_image else ("multi_image2image" if is_multi_reference else "image2image")
        }
    
    def _download_image(self, image_url: str, filename: str = None) -> str:
        """
        下载图片到本地
        
        Args:
            image_url: 图片 URL
            filename: 文件名 (可选)
            
        Returns:
            本地文件路径
        """
        if filename is None:
            filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        
        local_path = os.path.join(self.image_dir, filename)
        
        # 下载图片
        resp = requests.get(image_url, timeout=30)
        if resp.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return local_path
        else:
            raise Exception(f"图片下载失败：{resp.status_code}")
    
    def _should_retry(self, error_msg: str, attempt: int, max_retries: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            error_msg: 错误信息
            attempt: 当前尝试次数
            max_retries: 最大重试次数
            
        Returns:
            是否应该重试
        """
        # 不重试的错误
        permanent_errors = [
            "invalid_api_key",
            "authentication",
            "permission",
            "forbidden",
            "invalid_prompt",
            "content_policy"
        ]
        
        for error in permanent_errors:
            if error.lower() in error_msg.lower():
                return False
        
        # 可重试的错误
        retryable_errors = [
            "timeout",
            "rate limit",
            "service unavailable",
            "internal server",
            "connection",
            "network"
        ]
        
        for error in retryable_errors:
            if error.lower() in error_msg.lower():
                return True
        
        # 默认重试 500 系列错误
        return attempt < max_retries - 1


class CostTracker:
    """成本跟踪器"""
    
    def __init__(self):
        """初始化成本跟踪器"""
        self.sessions = []
        self.session_start = datetime.now()
        
        # 成本估算 (单位：元)
        # 注意：这些是估算值，实际成本请参考豆包官方定价
        self.estimated_costs = {
            "2K": 0.01,
            "4K": 0.02,
        }
    
    def record_generation(
        self,
        model: str,
        size: str,
        image_count: int = 0,
        generation_type: str = "single"
    ) -> Dict[str, Any]:
        """
        记录生成成本
        
        Args:
            model: 模型 ID
            size: 图片尺寸
            image_count: 参考图片数量 (文生图为 0)
            generation_type: 生成类型 (text2image/single/multi)
            
        Returns:
            成本信息
        """
        base_cost = self.estimated_costs.get(size, 0.01)
        
        # 多图参考可能增加成本
        if image_count > 1:
            base_cost *= (1 + (image_count - 1) * 0.2)
        elif image_count == 1:
            # 单图参考略高于文生图
            base_cost *= 1.1
        
        cost_info = {
            "model": model,
            "size": size,
            "generation_type": generation_type,
            "reference_images": image_count,
            "estimated_cost_cny": round(base_cost, 4),
            "timestamp": datetime.now().isoformat()
        }
        
        self.sessions.append(cost_info)
        
        return cost_info
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        获取当前会话成本摘要
        
        Returns:
            成本摘要
        """
        total_cost = sum(s["estimated_cost_cny"] for s in self.sessions)
        
        # 按类型统计
        type_counts = {}
        for s in self.sessions:
            t = s["generation_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "session_start": self.session_start.isoformat(),
            "total_generations": len(self.sessions),
            "by_type": type_counts,
            "total_estimated_cost_cny": round(total_cost, 4),
            "sessions": self.sessions
        }
    
    def reset(self):
        """重置成本跟踪"""
        self.sessions = []
        self.session_start = datetime.now()


def main():
    """测试脚本"""
    import argparse
    
    parser = argparse.ArgumentParser(description="豆包图像生成 API 测试 (文生图 + 图生图)")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 文生图
    text_parser = subparsers.add_parser("text", help="文生图")
    text_parser.add_argument("prompt", help="提示词")
    text_parser.add_argument("--size", default="2K", help="图片尺寸")
    text_parser.add_argument("--watermark", action="store_true", help="添加水印")
    text_parser.add_argument("--no-save", action="store_true", help="不保存到本地")
    
    # 单图生图
    single_parser = subparsers.add_parser("single", help="单图参考生图")
    single_parser.add_argument("prompt", help="提示词")
    single_parser.add_argument("image_url", help="参考图片 URL")
    single_parser.add_argument("--size", default="2K", help="图片尺寸")
    single_parser.add_argument("--watermark", action="store_true", help="添加水印")
    single_parser.add_argument("--no-save", action="store_true", help="不保存到本地")
    
    # 多图生图
    multi_parser = subparsers.add_parser("multi", help="多图参考生图")
    multi_parser.add_argument("prompt", help="提示词")
    multi_parser.add_argument("image_urls", nargs="+", help="参考图片 URL 列表")
    multi_parser.add_argument("--size", default="2K", help="图片尺寸")
    multi_parser.add_argument("--watermark", action="store_true", help="添加水印")
    multi_parser.add_argument("--sequential", default="disabled", 
                             choices=["disabled", "enabled"],
                             help="顺序图像生成")
    multi_parser.add_argument("--no-save", action="store_true", help="不保存到本地")
    
    args = parser.parse_args()
    
    # 初始化客户端
    client = DoubaoImageClient()
    
    save_locally = not hasattr(args, 'no_save') or not args.no_save
    
    if args.command == "text":
        result = client.text_to_image(
            prompt=args.prompt,
            size=args.size,
            watermark=args.watermark,
            save_locally=save_locally
        )
    
    elif args.command == "single":
        result = client.single_image_to_image(
            prompt=args.prompt,
            image_url=args.image_url,
            size=args.size,
            watermark=args.watermark,
            save_locally=save_locally
        )
    
    elif args.command == "multi":
        result = client.multi_image_to_image(
            prompt=args.prompt,
            image_urls=args.image_urls,
            size=args.size,
            watermark=args.watermark,
            sequential_generation=args.sequential,
            save_locally=save_locally
        )
    
    else:
        parser.print_help()
        return
    
    # 输出结果
    print("\n" + "=" * 50)
    print("结果:")
    print("=" * 50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 输出成本摘要
    if result.get("success"):
        summary = client.cost_tracker.get_session_summary()
        print("\n成本摘要:")
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
