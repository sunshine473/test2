#!/usr/bin/env python3
"""
Video Analyzer - Core engine for viral video analysis
Downloads, compresses, and analyzes videos using Gemini or Doubao API
"""

import sys
import os
import json
import base64
import subprocess
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Size limits
TARGET_SIZE_MB = 35
MAX_BASE64_SIZE_MB = 50
BYTES_PER_MB = 1024 * 1024

def log(msg):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr)

# API Configuration - Auto-detect available API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DOUBAO_API_KEY = os.environ.get("DOUBAO_API_KEY")

# Choose API based on availability
if GEMINI_API_KEY:
    API_PROVIDER = "gemini"
    API_KEY = GEMINI_API_KEY
    API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    API_MODEL = "gemini-2.5-flash"
elif DOUBAO_API_KEY:
    API_PROVIDER = "doubao"
    API_KEY = DOUBAO_API_KEY
    API_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/responses"
    API_MODEL = "doubao-seed-2-0-pro-260215"
else:
    API_PROVIDER = None
    API_KEY = None
    log("Warning: No API key found. Set GEMINI_API_KEY or DOUBAO_API_KEY environment variable.")

def detect_platform(url):
    """Detect video platform from URL"""
    if 'bilibili.com' in url or 'b23.tv' in url:
        return 'bilibili'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
        return 'xiaohongshu'
    elif 'douyin.com' in url:
        return 'douyin'
    return 'unknown'

def download_video(url, output_path):
    """Download video using yt-dlp"""
    platform = detect_platform(url)

    # Xiaohongshu and Douyin not supported by yt-dlp, exit with code 2
    if platform in ['xiaohongshu', 'douyin']:
        log(f"Platform {platform} requires browser fallback")
        sys.exit(2)

    log(f"Downloading from {platform}...")

    # Use yt-dlp with 720p limit
    cmd = [
        'yt-dlp',
        '-f', 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '--merge-output-format', 'mp4',
        '-o', output_path,
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Check for anti-crawler errors
            if '412' in result.stderr or '403' in result.stderr:
                log("Anti-crawler detected, need browser fallback")
                sys.exit(2)
            raise Exception(f"yt-dlp failed: {result.stderr}")
        log(f"Downloaded to {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        raise Exception("Download timeout (5 minutes)")
    except FileNotFoundError:
        raise Exception("yt-dlp not found. Install with: pip install yt-dlp")

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_video_size_mb(video_path):
    """Get video file size in MB"""
    return os.path.getsize(video_path) / BYTES_PER_MB

def estimate_base64_size_mb(video_path):
    """Estimate base64 encoded size"""
    file_size = os.path.getsize(video_path)
    base64_size = file_size * 4 / 3  # Base64 encoding overhead
    return base64_size / BYTES_PER_MB

def compress_video(input_path, output_path, target_size_mb=TARGET_SIZE_MB, aggressive=False):
    """Compress video to target size using ffmpeg"""
    duration = get_video_duration(input_path)
    current_size_mb = get_video_size_mb(input_path)
    estimated_base64_mb = estimate_base64_size_mb(input_path)

    log(f"Video: {duration:.1f}s, {current_size_mb:.1f}MB, base64: ~{estimated_base64_mb:.1f}MB")

    # If already small enough and base64 fits, just do faststart
    if current_size_mb < target_size_mb and estimated_base64_mb < MAX_BASE64_SIZE_MB:
        log("Video already small enough, applying faststart only...")
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    # Calculate target bitrate
    if aggressive:
        target_size_mb = target_size_mb * 0.7  # More aggressive

    target_size_bits = target_size_mb * BYTES_PER_MB * 8
    target_bitrate = int(target_size_bits / duration * 0.95)  # 95% for audio overhead

    log(f"Compressing to ~{target_size_mb:.1f}MB (bitrate: {target_bitrate}bps)...")

    # Get video dimensions
    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=height',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    height = int(subprocess.run(probe_cmd, capture_output=True, text=True).stdout.strip())

    # Build ffmpeg command
    cmd = [
        'ffmpeg', '-i', input_path,
        '-c:v', 'libx264',
        '-b:v', str(target_bitrate),
        '-maxrate', str(int(target_bitrate * 1.2)),
        '-bufsize', str(int(target_bitrate * 2)),
        '-preset', 'medium',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart'
    ]

    # Scale down if height > 720
    if height > 720:
        cmd.extend(['-vf', 'scale=-2:720'])

    cmd.extend(['-y', output_path])

    subprocess.run(cmd, capture_output=True, check=True)

    # Check if base64 still exceeds limit
    new_base64_mb = estimate_base64_size_mb(output_path)
    log(f"Compressed: {get_video_size_mb(output_path):.1f}MB, base64: ~{new_base64_mb:.1f}MB")

    if new_base64_mb > MAX_BASE64_SIZE_MB and not aggressive:
        log("Base64 still too large, doing aggressive second pass...")
        temp_path = output_path + '.tmp.mp4'
        os.rename(output_path, temp_path)
        compress_video(temp_path, output_path, target_size_mb, aggressive=True)
        os.remove(temp_path)

    return output_path

def video_to_base64_data_url(video_path):
    """Convert video to base64 data URL"""
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    base64_str = base64.b64encode(video_bytes).decode('utf-8')
    return f"data:video/mp4;base64,{base64_str}"

def call_api(video_data_url, prompt, max_retries=3):
    """Call video analysis API (Gemini or Doubao)"""
    import urllib.request

    if not API_KEY:
        raise Exception("No API key configured. Set GEMINI_API_KEY or DOUBAO_API_KEY environment variable.")

    for attempt in range(max_retries):
        try:
            log(f"Calling {API_PROVIDER.upper()} API (attempt {attempt + 1}/{max_retries})...")

            if API_PROVIDER == "gemini":
                # Gemini API format
                # Extract base64 from data URL
                base64_video = video_data_url.split(',')[1]

                payload = {
                    "contents": [{
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "video/mp4",
                                    "data": base64_video
                                }
                            },
                            {"text": prompt}
                        ]
                    }]
                }

                url = f"{API_ENDPOINT}?key={API_KEY}"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )

            else:  # doubao
                # Doubao API format
                payload = {
                    "model": API_MODEL,
                    "input": [{
                        "role": "user",
                        "content": [
                            {"type": "input_video", "video_url": video_data_url},
                            {"type": "input_text", "text": prompt}
                        ]
                    }]
                }

                req = urllib.request.Request(
                    API_ENDPOINT,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {API_KEY}'
                    }
                )

            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode('utf-8'))
                return parse_api_response(result)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            log(f"API call failed: HTTP {e.code} - {error_body[:500]}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise Exception(f"API failed after {max_retries} attempts: {error_body[:500]}")
        except Exception as e:
            log(f"API call failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def parse_api_response(response):
    """Parse API response (handle Gemini and Doubao formats)"""
    text = None

    # Gemini format
    if 'candidates' in response:
        text = response['candidates'][0]['content']['parts'][0]['text']

    # Doubao Format 1: responses API format
    elif 'output' in response and isinstance(response['output'], list):
        for item in response['output']:
            if item.get('type') == 'message':
                content = item.get('content', [])
                for c in content:
                    if c.get('type') == 'output_text':
                        text = c.get('text')
                        break

    # Doubao Format 2: output as dict
    elif 'output' in response and isinstance(response['output'], dict):
        text = response['output'].get('text')

    # Doubao Format 3: chat completions format
    elif 'choices' in response:
        text = response['choices'][0]['message']['content']

    if not text:
        raise Exception(f"Cannot parse API response: {json.dumps(response)[:200]}")

    # Log the raw text for debugging
    log(f"Raw API response text (first 200 chars): {text[:200]}")

    # Extract JSON from markdown code blocks
    if '```json' in text:
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    elif '```' in text:
        match = re.search(r'```\s*([\s\S]*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Extract outermost JSON object or array using brace matching
    text = text.strip()

    if not text:
        raise Exception("Empty text after extraction")

    if text.startswith('{'):
        brace_count = 0
        for i, char in enumerate(text):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    text = text[:i+1]
                    break
    elif text.startswith('['):
        brace_count = 0
        for i, char in enumerate(text):
            if char == '[':
                brace_count += 1
            elif char == ']':
                brace_count -= 1
                if brace_count == 0:
                    text = text[:i+1]
                    break
    else:
        # Try to find JSON object or array anywhere in the text
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if json_match:
            text = json_match.group(1)
        else:
            raise Exception(f"No JSON found in text: {text[:200]}")

    return json.loads(text)

def get_analysis_prompt():
    """Get the 8-dimension + 5-module analysis prompt"""
    return """你是爆款视频分析专家。请对这个视频进行全面分析，输出完整的 JSON 格式结果。

**重要评分指令**：
你必须基于视频的实际质量独立评分，不要受到示例格式中任何数字的影响。评分应有明显区分度：
- 1-3分：差，明显不足，业余水平
- 4-5分：一般，有基本功但缺乏亮点
- 6-7分：良好，有一定专业度和创意
- 8-9分：优秀，接近头部水平
- 10分：顶级，教科书级别（极少给出）

overall_score 应该是8个维度评分的加权平均（hook和narrative权重更高），不要简单给一个笼统的高分。
差的视频就应该给低分（3-5分），一般的给中间分（5-7分），只有真正优秀的才给8分以上。

请按以下结构输出 JSON：

{
  "overall_score": <1-10的数字，8维度加权平均>,
  "summary": "整体评价（2-3句话）",

  "dimensions": {
    "hook": {
      "score": <1-10>,
      "description": "开头吸引力分析",
      "formula": "使用的钩子公式",
      "template": "可复制的开头模板"
    },
    "narrative": {
      "score": <1-10>,
      "type": "叙事类型（如：问题-解决、对比、故事）",
      "description": "叙事结构分析",
      "timeline": [
        {"time": "0:00-0:15", "chapter": "章节名", "purpose": "作用"}
      ],
      "template": "叙事结构模板"
    },
    "pacing": {
      "score": <1-10>,
      "description": "节奏感分析",
      "cut_points": ["0:03", "0:08", "0:15"],
      "pattern": "节奏模式描述"
    },
    "visual": {
      "score": <1-10>,
      "description": "视觉构图分析",
      "shots": [
        {"time": "0:00", "type": "特写/中景/远景", "composition": "构图描述"}
      ],
      "color_style": "色彩风格",
      "effects": ["转场1", "特效2"]
    },
    "text_overlay": {
      "score": <1-10>,
      "description": "字幕设计分析",
      "has_text": true/false,
      "style": "字幕风格描述",
      "highlights": ["0:05 关键词高亮", "0:12 emoji"]
    },
    "audio": {
      "score": <1-10>,
      "description": "音乐音效分析",
      "estimated_bpm": <数字或null>,
      "sync_evidence": "音画同步证据",
      "voice_style": "配音风格"
    },
    "cta": {
      "score": <1-10>,
      "description": "互动引导分析",
      "has_cta": true/false,
      "cta_time": "出现时间",
      "cta_type": "点赞/评论/关注/分享"
    },
    "ending": {
      "score": <1-10>,
      "description": "结尾设计分析",
      "is_loopable": true/false,
      "has_series_hook": true/false,
      "ending_type": "结尾类型"
    }
  },

  "advanced_modules": {
    "emotional_arc": {
      "arc_type": "情绪弧线类型（如：上升型、波动型、反转型）",
      "arc_description": "情绪弧线描述",
      "curve_points": [
        {"time": "0:00", "valence": 0, "arousal": 5, "label": "平静开场"}
      ],
      "turning_points": [
        {"time": "0:15", "type": "冲突/高潮/反转", "description": "转折点描述"}
      ]
    },
    "retention_prediction": {
      "hook_rate_3s": <0-100>,
      "retention_30s": <0-100>,
      "midpoint_retention": <0-100>,
      "completion_rate": <0-100>,
      "risk_segments": [
        {"time": "0:45-1:00", "risk": "high/medium/low", "label": "风险标签", "reason": "原因", "fix": "修复建议"}
      ]
    },
    "viral_formulas": {
      "script_formula": {
        "steps": ["步骤1", "步骤2"],
        "fill_template": "可填空的文案模板"
      },
      "emotion_formula": {
        "nodes": ["情绪节点1", "情绪节点2"],
        "key_principles": ["原则1", "原则2"]
      },
      "algorithm_formula": {
        "drivers": ["完播率驱动因素1", "互动驱动因素2"],
        "weight_tips": ["权重建议1", "权重建议2"]
      }
    },
    "algorithm_fitness": {
      "metrics": {
        "completion_rate": <0-100>,
        "interaction_rate": <0-100>,
        "share_rate": <0-100>,
        "save_rate": <0-100>
      },
      "platform_fit": [
        {"platform": "抖音", "score": <1-10>, "reason": "原因", "recommended": true/false}
      ]
    },
    "learning_path": [
      {
        "rank": 1,
        "technique": "技巧名称",
        "difficulty": "初级/中级/高级",
        "why": "为什么要学这个",
        "exercises": ["练习任务1", "练习任务2"],
        "reference": "参考案例"
      }
    ]
  },

  "replicable_template": {
    "structure": "结构公式（如：钩子(3s) + 问题(10s) + 方案(30s) + CTA(5s)）",
    "shot_list": [
      {"shot": 1, "duration": "3s", "type": "特写", "content": "拍什么", "note": "注意事项"}
    ],
    "script_template": "文案模板（带填空）"
  },

  "top3_strengths": ["亮点1", "亮点2", "亮点3"],
  "top3_improvements": ["改进建议1", "改进建议2", "改进建议3"]
}

请确保输出完整有效的 JSON，不要有任何额外文字。"""

def get_scene_breakdown_prompt(analysis_result):
    """Get scene-level breakdown prompt"""
    timeline = analysis_result.get('dimensions', {}).get('narrative', {}).get('timeline', [])
    timeline_str = json.dumps(timeline, ensure_ascii=False, indent=2)

    return f"""基于之前的整体分析，现在请对视频进行逐场景细拆。

之前识别的章节分段：
{timeline_str}

请对每个章节按 15-25 秒粒度拆分为多个 scene，输出 JSON 数组：

[
  {{
    "chapter": "章节名（对应上面的timeline）",
    "time_range": "0:00-0:15",
    "scenes": [
      {{
        "time": "0:00-0:08",
        "visual": "画面描述（镜头、构图、主体）",
        "audio": "音频描述（BGM、音效、台词节奏）",
        "emotion": "情绪标签（如：好奇、紧张、兴奋）",
        "emotion_valence": <-5到+5的数字，负数=负面，正数=正面>,
        "emotion_arousal": <0到10的数字，唤醒度/激烈程度>,
        "retention_risk": "low/medium/high",
        "risk_reason": "如果有风险，说明原因（如：画面单一超15秒、纯文字无变化）",
        "risk_fix": "修复建议",
        "quote": "这段的关键台词或文案（如有）",
        "techniques": [
          {{"name": "技巧名", "category": "Hook/留存/节奏/情绪/信任/互动/视觉", "why": "为什么有效"}}
        ]
      }}
    ]
  }}
]

retention_risk 判断标准：
- 画面单一超15秒 = medium
- 纯文字无变化超20秒 = high
- 抽象概念无类比/可视化 = medium
- 信息密度过低 = medium

请确保输出完整有效的 JSON 数组，不要有任何额外文字。"""

def analyze_video(video_path, video_data_url):
    """Perform 8-dimension + 5-module analysis"""
    log("Step 3: Performing 8-dimension analysis...")
    prompt1 = get_analysis_prompt()
    analysis = call_api(video_data_url, prompt1)

    log("Step 4: Performing scene-level breakdown...")
    prompt2 = get_scene_breakdown_prompt(analysis)
    scenes = call_api(video_data_url, prompt2)

    # Merge scenes into analysis
    analysis['scene_breakdown'] = scenes

    return analysis

def extract_frames(video_path, output_dir, interval=20):
    """Extract frames at regular intervals for timeline visualization"""
    os.makedirs(output_dir, exist_ok=True)
    duration = get_video_duration(video_path)

    frames = []
    current_time = 0
    frame_index = 0

    while current_time < duration:
        output_path = os.path.join(output_dir, f"frame_{frame_index:03d}.jpg")
        cmd = [
            'ffmpeg',
            '-ss', str(current_time),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        frames.append({
            'time': current_time,
            'path': output_path,
            'time_str': f"{int(current_time // 60)}:{int(current_time % 60):02d}"
        })

        current_time += interval
        frame_index += 1

    return frames

def generate_slug(title):
    """Generate ASCII-only slug from title"""
    # Remove non-ASCII characters
    ascii_title = ''.join(c for c in title if ord(c) < 128)
    if ascii_title.strip():
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', ascii_title).strip('-')[:50]
    else:
        # Use MD5 hash for non-ASCII titles
        slug = hashlib.md5(title.encode('utf-8')).hexdigest()[:12]
    return slug

def run_full_pipeline(url_or_path, title=None, archive_dir=None):
    """Run complete analysis pipeline"""
    # Setup paths
    temp_dir = Path('/tmp/video_analyzer')
    temp_dir.mkdir(exist_ok=True)

    # Step 1: Download or use local file
    if os.path.exists(url_or_path):
        log(f"Using local file: {url_or_path}")
        video_path = url_or_path
    else:
        video_path = str(temp_dir / 'downloaded.mp4')
        download_video(url_or_path, video_path)

    # Step 2: Compress
    compressed_path = str(temp_dir / 'compressed.mp4')
    compress_video(video_path, compressed_path)

    # Convert to base64
    log("Converting to base64...")
    video_data_url = video_to_base64_data_url(compressed_path)

    # Step 3 & 4: Analyze
    analysis = analyze_video(compressed_path, video_data_url)

    # Step 5: Generate report
    if not title:
        title = analysis.get('summary', 'Untitled Video')[:50]

    if archive_dir:
        archive_dir = Path(archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create dated subdirectory
        date_str = datetime.now().strftime('%Y-%m-%d')
        slug = generate_slug(title)
        report_dir = archive_dir / f"{date_str}_{slug}"
        report_dir.mkdir(exist_ok=True)

        # Extract frames
        frames_dir = report_dir / 'frames'
        log("Extracting frames for timeline...")
        frames = extract_frames(compressed_path, str(frames_dir))

        # Copy compressed video
        import shutil
        video_dest = report_dir / 'video.mp4'
        shutil.copy2(compressed_path, video_dest)

        # Generate HTML report
        log("Generating HTML report...")
        from report_generator import generate_report
        generate_report(
            analysis_data=analysis,
            video_path=video_dest,
            frames=frames,
            output_dir=report_dir,
            title=title
        )

        log(f"✓ Report saved to: {report_dir}")
        print(str(report_dir / 'report.html'))  # Output path for SKILL.md
    else:
        # Just output JSON
        print(json.dumps(analysis, ensure_ascii=False, indent=2))

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Video Analyzer')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # run command (full pipeline)
    run_parser = subparsers.add_parser('run', help='Run full analysis pipeline')
    run_parser.add_argument('input', help='Video URL or local path')
    run_parser.add_argument('--title', help='Video title')
    run_parser.add_argument('--archive-dir', help='Archive directory for reports')

    # download command
    dl_parser = subparsers.add_parser('download', help='Download video only')
    dl_parser.add_argument('url', help='Video URL')
    dl_parser.add_argument('--output', default='video.mp4', help='Output path')

    # compress command
    comp_parser = subparsers.add_parser('compress', help='Compress video only')
    comp_parser.add_argument('input', help='Input video path')
    comp_parser.add_argument('--output', default='compressed.mp4', help='Output path')

    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze video only (output JSON)')
    analyze_parser.add_argument('input', help='Video path')

    args = parser.parse_args()

    if args.command == 'run':
        run_full_pipeline(args.input, args.title, args.archive_dir)
    elif args.command == 'download':
        download_video(args.url, args.output)
    elif args.command == 'compress':
        compress_video(args.input, args.output)
    elif args.command == 'analyze':
        video_data_url = video_to_base64_data_url(args.input)
        analysis = analyze_video(args.input, video_data_url)
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
