"""
视频上传模块 - 用于将视频上传到 Cloudflare R2
"""

import os
import requests
import time
from pathlib import Path
from typing import Optional


def load_r2_config(config_file: Path = None) -> dict:
    """Load R2 upload configuration from config.ini"""
    import configparser
    
    default_config = {
        "worker_url": "https://ashuaiz.dpdns.org",
        "api_key": "vt_default_key_for_testing"
    }
    
    if config_file is None:
        config_file = Path(__file__).parent / "config.ini"
    
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")
        
        # Read from [R2] section
        worker_url = config.get("R2", "WORKER_URL", fallback=default_config["worker_url"])
        api_key = config.get("R2", "API_KEY", fallback=default_config["api_key"])
        
        return {
            "worker_url": worker_url,
            "api_key": api_key
        }
    
    return default_config


def upload_video_to_r2(
    video_path: str,
    worker_url: str = None,
    api_key: str = None,
    custom_filename: str = None
) -> str:
    """
    Upload video to R2 and return public URL
    
    Args:
        video_path: Path to video file
        worker_url: R2 worker URL (optional, loads from config if not provided)
        api_key: API key (optional, loads from config if not provided)
        custom_filename: Custom filename (optional)
    
    Returns:
        Public URL of uploaded video, or empty string if failed
    """
    # Load config if not provided
    if worker_url is None or api_key is None:
        config = load_r2_config()
        worker_url = worker_url or config["worker_url"]
        api_key = api_key or config["api_key"]
    
    # Validate video path
    if not video_path or not os.path.exists(video_path):
        print(f"[VideoUploader] ❌ Video file not found: {video_path}")
        return ""
    
    # Determine filename
    if custom_filename and custom_filename.strip():
        filename = custom_filename.strip()
        if not any(filename.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']):
            filename += '.mp4'
    else:
        timestamp = int(time.time())
        original_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_{timestamp}.mp4"
    
    try:
        print(f"[VideoUploader] 🚀 Uploading video: {filename}")
        
        # Step 1: Get upload URL from Worker
        upload_url_endpoint = f"{worker_url}/get-upload-url?file={filename}&api_key={api_key}"
        
        response = requests.get(upload_url_endpoint, timeout=30)
        response.raise_for_status()
        
        upload_data = response.json()
        presigned_url = upload_data['uploadUrl']
        public_url = upload_data['publicUrl']
        
        print(f"[VideoUploader] ✅ Got presigned URL")
        
        # Step 2: Upload file to R2
        file_size = os.path.getsize(video_path)
        print(f"[VideoUploader] 📤 Uploading {file_size / 1024 / 1024:.2f} MB...")
        
        with open(video_path, 'rb') as f:
            headers = {'Content-Type': 'video/mp4'}
            upload_response = requests.put(
                presigned_url,
                data=f,
                headers=headers,
                timeout=300
            )
            upload_response.raise_for_status()
        
        print(f"[VideoUploader] ✅ Upload successful: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"[VideoUploader] ❌ Upload failed: {e}")
        return ""


def upload_videos(
    video_paths: list,
    worker_url: str = None,
    api_key: str = None
) -> list:
    """
    Upload multiple videos to R2
    
    Args:
        video_paths: List of video file paths
        worker_url: R2 worker URL (optional)
        api_key: API key (optional)
    
    Returns:
        List of public URLs for successfully uploaded videos
    """
    if not video_paths:
        print("[VideoUploader] 警告: 没有输入任何视频")
        return []
    
    print(f"[VideoUploader] 开始上传 {len(video_paths)} 个视频...")
    
    uploaded_urls = []
    for i, video_path in enumerate(video_paths):
        try:
            if video_path and os.path.exists(str(video_path)):
                url = upload_video_to_r2(str(video_path), worker_url, api_key)
                if url:
                    uploaded_urls.append(url)
                    print(f"[VideoUploader] 视频 {i+1}/{len(video_paths)} 上传成功")
                else:
                    print(f"[VideoUploader] 视频 {i+1}/{len(video_paths)} 上传失败")
            else:
                print(f"[VideoUploader] 视频 {i+1}/{len(video_paths)} 路径无效: {video_path}")
        except Exception as e:
            print(f"[VideoUploader] 处理视频 {i+1} 失败: {e}")
    
    print(f"[VideoUploader] 完成: {len(uploaded_urls)}/{len(video_paths)} 个视频上传成功")
    return uploaded_urls


if __name__ == "__main__":
    # Test upload
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_uploader.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    url = upload_video_to_r2(video_path)
    
    if url:
        print(f"\n视频上传成功！")
        print(f"URL: {url}")
    else:
        print(f"\n视频上传失败！")
        sys.exit(1)
