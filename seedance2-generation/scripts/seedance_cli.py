#!/usr/bin/env python3
"""
Seedance 2.0 Video Generation CLI Tool
"""

import argparse
import base64
import configparser
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Image processing will be limited.")

try:
    from volcenginesdkarkruntime import Ark
    ARK_SDK_AVAILABLE = True
except ImportError:
    ARK_SDK_AVAILABLE = False
    print("Error: volcengine-python-sdk[ark] not installed.")
    print("Install with: pip install 'volcengine-python-sdk[ark]'")
    sys.exit(1)

# Constants
CONFIG_FILE = Path(__file__).parent / "config.ini"
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3"
POLL_INTERVAL = 3  # seconds
MAX_POLLS = 200

# Default models
MODELS = {
    "seedance-2-0": "doubao-seedance-2-0-260128",
    "seedance-2-0-fast": "doubao-seedance-2-0-fast-260128"
}


def load_config() -> configparser.ConfigParser:
    """Load or create config file"""
    config = configparser.ConfigParser()
    
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")
    
    # Ensure required sections exist
    if "API" not in config:
        config["API"] = {}
    if "Settings" not in config:
        config["Settings"] = {}
    
    return config


def save_config(config: configparser.ConfigParser):
    """Save config to file"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)


def setup_config_wizard():
    """Interactive configuration wizard for first run"""
    print("=" * 60)
    print("Seedance Video Generator - First Time Setup")
    print("=" * 60)
    print()
    
    config = load_config()
    
    # Check if API key exists
    api_key = config.get("API", "ARK_API_KEY", fallback="")
    if not api_key:
        print("Please enter your ARK API Key.")
        print("You can get it from: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey")
        print()
        api_key = input("ARK_API_KEY: ").strip()
        if api_key:
            config["API"]["ARK_API_KEY"] = api_key
            print("✓ API Key saved")
        else:
            print("✗ API Key is required")
            sys.exit(1)
    
    # Check if default resolution exists
    resolution = config.get("Settings", "RESOLUTION", fallback="")
    if not resolution:
        print()
        print("Select default video resolution:")
        print("  1. 480p")
        print("  2. 720p")
        choice = input("Enter choice (1-2) [2]: ").strip() or "2"
        resolution = "720p" if choice == "2" else "480p"
        config["Settings"]["RESOLUTION"] = resolution
        print(f"✓ Default resolution set to: {resolution}")
    
    # Check if default duration exists
    duration = config.get("Settings", "DURATION", fallback="")
    if not duration:
        print()
        print("Select default video duration (4-15 seconds):")
        while True:
            duration = input("Enter duration in seconds [11]: ").strip() or "11"
            try:
                duration_int = int(duration)
                if 4 <= duration_int <= 15:
                    config["Settings"]["DURATION"] = duration
                    print(f"✓ Default duration set to: {duration} seconds")
                    break
                else:
                    print("Duration must be between 4 and 15 seconds")
            except ValueError:
                print("Please enter a valid number")
    
    # Check if default model exists
    model = config.get("Settings", "MODEL", fallback="")
    if not model:
        print()
        print("Select default model:")
        print("  1. seedance-2-0-fast (faster generation)")
        print("  2. seedance-2-0 (higher quality)")
        choice = input("Enter choice (1-2) [1]: ").strip() or "1"
        model = "seedance-2-0-fast" if choice == "1" else "seedance-2-0"
        config["Settings"]["MODEL"] = model
        print(f"✓ Default model set to: {model}")
    
    # Save config
    save_config(config)
    print()
    print("=" * 60)
    print("Setup complete! Configuration saved to config.ini")
    print("=" * 60)
    print()
    
    return config


def get_ark_client(config: configparser.ConfigParser) -> Ark:
    """Get Ark client with API key"""
    api_key = config.get("API", "ARK_API_KEY", fallback="")
    
    if not api_key:
        api_key = os.environ.get("ARK_API_KEY", "")
    
    if not api_key:
        print("Error: ARK_API_KEY not found in config.ini or environment variables")
        print("Please run the setup wizard or set ARK_API_KEY environment variable")
        sys.exit(1)
    
    return Ark(
        base_url=ARK_API_URL,
        api_key=api_key
    )


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    if not CV2_AVAILABLE:
        # Fallback: read raw file and encode
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    # Use OpenCV for proper image processing
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Encode as JPEG
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode("utf-8")


def audio_to_base64(audio_path: str) -> str:
    """Convert audio file to base64 string"""
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def download_video(video_url: str, save_path: str) -> bool:
    """Download video from URL to local path"""
    try:
        req = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(save_path, "wb") as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def generate_video(
    client: Ark,
    prompt: str,
    model: str,
    resolution: str,
    ratio: str,
    duration: int,
    generate_audio: bool,
    image_paths: List[str],
    audio_paths: List[str],
    output_dir: str = None
) -> Tuple[bool, str]:
    """
    Generate video using Seedance API
    
    Returns:
        (success: bool, message: str)
    """
    # Set default output directory to SKILL directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "output"
    
    # Validate inputs
    if len(image_paths) > 9:
        print(f"Warning: Too many images ({len(image_paths)}), using first 9")
        image_paths = image_paths[:9]
    
    if len(audio_paths) > 3:
        print(f"Warning: Too many audio files ({len(audio_paths)}), using first 3")
        audio_paths = audio_paths[:3]
    
    # Process images
    print(f"Processing {len(image_paths)} image(s)...")
    image_base64_list = []
    for i, img_path in enumerate(image_paths):
        try:
            img_base64 = image_to_base64(img_path)
            image_base64_list.append(img_base64)
            print(f"  ✓ Image {i+1}: {img_path}")
        except Exception as e:
            print(f"  ✗ Image {i+1} failed: {e}")
    
    # Process audio
    print(f"Processing {len(audio_paths)} audio file(s)...")
    audio_base64_list = []
    for i, audio_path in enumerate(audio_paths):
        try:
            audio_base64 = audio_to_base64(audio_path)
            audio_base64_list.append(audio_base64)
            print(f"  ✓ Audio {i+1}: {audio_path}")
        except Exception as e:
            print(f"  ✗ Audio {i+1} failed: {e}")
    
    # Build content
    content = []
    
    # Add text prompt
    content.append({
        "type": "text",
        "text": prompt
    })
    
    # Add images
    for img_base64 in image_base64_list:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_base64}"
            },
            "role": "reference_image"
        })
    
    # Add audio
    for audio_base64 in audio_base64_list:
        content.append({
            "type": "audio_url",
            "audio_url": {
                "url": f"data:audio/wav;base64,{audio_base64}"
            },
            "role": "reference_audio"
        })
    
    # Build request parameters
    create_kwargs = {
        "model": model,
        "content": content,
        "ratio": ratio,
        "duration": duration,
        "watermark": False,
    }
    
    if resolution:
        create_kwargs["resolution"] = resolution
    
    if generate_audio:
        create_kwargs["generate_audio"] = True
    
    # Create task
    print()
    print("=" * 60)
    print("Creating video generation task...")
    print(f"  Model: {model}")
    print(f"  Resolution: {resolution}")
    print(f"  Ratio: {ratio}")
    print(f"  Duration: {duration}s")
    print(f"  Generate Audio: {generate_audio}")
    print(f"  Images: {len(image_base64_list)}")
    print(f"  Audios: {len(audio_base64_list)}")
    print("=" * 60)
    
    try:
        create_result = client.content_generation.tasks.create(**create_kwargs)
        task_id = create_result.id
        print(f"✓ Task created: {task_id}")
    except Exception as e:
        return False, f"Failed to create task: {e}"
    
    # Poll for task completion
    print()
    print("Polling task status...")
    poll_count = 0
    video_url = None
    
    while poll_count < MAX_POLLS:
        time.sleep(POLL_INTERVAL)
        poll_count += 1
        
        try:
            get_result = client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            
            if status == "succeeded":
                print(f"✓ Task completed!")
                video_url = get_result.content.video_url
                break
            elif status == "failed":
                error_msg = "Task failed"
                if hasattr(get_result, 'error') and get_result.error:
                    error_msg += f": {get_result.error}"
                return False, error_msg
            else:
                print(f"  Status: {status} ({poll_count}/{MAX_POLLS}), retrying in {POLL_INTERVAL}s...")
        except Exception as e:
            print(f"  Query failed: {e}, retrying...")
            continue
    
    if not video_url:
        return False, "Timeout: Video generation did not complete"
    
    # Download video
    print()
    print(f"Downloading video...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = int(time.time())
    video_filename = f"seedance_{timestamp}.mp4"
    video_path = output_path / video_filename
    
    if not download_video(video_url, str(video_path)):
        return False, f"Failed to download video from: {video_url}"
    
    # Get absolute path for display
    video_path_absolute = video_path.resolve()
    
    print()
    print("=" * 60)
    print("✓ VIDEO GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📁 Video saved to: {video_path_absolute}")
    print("=" * 60)
    
    # Build result info
    result_info = f"""
Seedance Video Generation Successful
{'=' * 60}
Task ID: {task_id}
Video URL: {video_url}
Local Path: {video_path_absolute}

Parameters:
  Model: {model}
  Resolution: {resolution}
  Ratio: {ratio}
  Duration: {duration}s
  Generate Audio: {generate_audio}
  Images: {len(image_base64_list)}
  Audios: {len(audio_base64_list)}

Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}
{'=' * 60}
"""
    
    return True, result_info


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Seedance 2.0 Video Generation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p "A beautiful sunset"
  %(prog)s -p "Dancing character" -i img1.jpg img2.jpg -a music.mp3
  %(prog)s -p "Product showcase" -i *.jpg -a bgm.mp3 -r 720p -d 10
        """
    )
    
    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="Video generation prompt (required)"
    )
    
    parser.add_argument(
        "-i", "--images",
        nargs="*",
        default=[],
        help="Image file paths (up to 9)"
    )
    
    parser.add_argument(
        "-a", "--audio",
        nargs="*",
        default=[],
        help="Audio file paths (up to 3)"
    )
    
    parser.add_argument(
        "-r", "--resolution",
        choices=["480p", "720p"],
        help="Video resolution (default: from config)"
    )
    
    parser.add_argument(
        "-d", "--duration",
        type=int,
        choices=range(4, 16),
        metavar="4-15",
        help="Video duration in seconds (default: from config)"
    )
    
    parser.add_argument(
        "--ratio",
        choices=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"],
        default="16:9",
        help="Aspect ratio (default: 16:9)"
    )
    
    parser.add_argument(
        "--generate-audio",
        action="store_true",
        default=True,
        help="Generate audio (default: True)"
    )
    
    parser.add_argument(
        "--no-generate-audio",
        dest="generate_audio",
        action="store_false",
        help="Disable audio generation"
    )
    
    parser.add_argument(
        "--model",
        choices=list(MODELS.keys()),
        default=None,
        help="Model to use (default: from config, fallback: seedance-2-0-fast)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory (default: SKILL directory)"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run configuration wizard"
    )
    
    args = parser.parse_args()
    
    # Load or setup config
    if args.setup or not CONFIG_FILE.exists():
        config = setup_config_wizard()
    else:
        config = load_config()
        # Check if we need to run setup
        if not config.get("API", "ARK_API_KEY", fallback=""):
            config = setup_config_wizard()
    
    # Get Ark client
    client = get_ark_client(config)
    
    # Get default values from config if not provided
    resolution = args.resolution or config.get("Settings", "RESOLUTION", fallback="720p")
    duration = args.duration or config.getint("Settings", "DURATION", fallback=11)
    
    # Get model from args or config, fallback to seedance-2-0-fast
    model_key = args.model or config.get("Settings", "MODEL", fallback="seedance-2-0-fast")
    model_name = MODELS[model_key]
    
    # Validate image files
    valid_images = []
    for img_path in args.images:
        path = Path(img_path)
        if path.exists():
            valid_images.append(str(path.resolve()))
        else:
            print(f"Warning: Image not found: {img_path}")
    
    # Validate audio files
    valid_audio = []
    for audio_path in args.audio:
        path = Path(audio_path)
        if path.exists():
            valid_audio.append(str(path.resolve()))
        else:
            print(f"Warning: Audio not found: {audio_path}")
    
    # Generate video
    success, message = generate_video(
        client=client,
        prompt=args.prompt,
        model=model_name,
        resolution=resolution,
        ratio=args.ratio,
        duration=duration,
        generate_audio=args.generate_audio,
        image_paths=valid_images,
        audio_paths=valid_audio,
        output_dir=args.output
    )
    
    print(message)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
