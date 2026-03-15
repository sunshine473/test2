#!/usr/bin/env python3
"""HTML report generator for video analysis results."""

import base64
import json
from pathlib import Path
from typing import Any, Dict, List


def generate_report(
    analysis_data: Dict[str, Any],
    video_path: Path,
    frames: List[Path],
    output_dir: Path,
    title: str = "视频分析报告"
) -> tuple[Path, Path]:
    """
    Generate HTML reports for video analysis.

    Args:
        analysis_data: Analysis results dictionary
        video_path: Path to video file
        frames: List of frame image paths
        output_dir: Output directory for reports
        title: Report title

    Returns:
        Tuple of (report.html path, report-lite.html path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate both versions
    full_report = output_dir / "report.html"
    lite_report = output_dir / "report-lite.html"

    # Read video as base64 for full report
    video_base64 = ""
    if video_path.exists():
        with open(video_path, "rb") as f:
            video_base64 = base64.b64encode(f.read()).decode()

    # Generate WebVTT for scene markers
    vtt_content = _generate_vtt(analysis_data.get("scenes", []))

    # Generate frame thumbnails HTML
    frames_html = _generate_frames_html(frames, analysis_data.get("scenes", []))

    # Generate radar chart data
    radar_data = _extract_radar_data(analysis_data)

    # Generate full report (self-contained)
    full_html = _generate_html_template(
        title=title,
        analysis_data=analysis_data,
        video_src=f"data:video/mp4;base64,{video_base64}",
        vtt_content=vtt_content,
        frames_html=frames_html,
        radar_data=radar_data,
        is_lite=False
    )

    with open(full_report, "w", encoding="utf-8") as f:
        f.write(full_html)

    # Generate lite report (references video.mp4)
    lite_html = _generate_html_template(
        title=title,
        analysis_data=analysis_data,
        video_src="video.mp4",
        vtt_content=vtt_content,
        frames_html=frames_html,
        radar_data=radar_data,
        is_lite=True
    )

    with open(lite_report, "w", encoding="utf-8") as f:
        f.write(lite_html)

    return full_report, lite_report


def _generate_vtt(scenes: List[Dict[str, Any]]) -> str:
    """Generate WebVTT content for scene markers."""
    vtt_lines = ["WEBVTT", ""]

    for i, scene in enumerate(scenes, 1):
        start = scene.get("timestamp", 0)
        end = scene.get("end_timestamp", start + 5)
        description = scene.get("description", f"Scene {i}")

        vtt_lines.append(f"{i}")
        vtt_lines.append(f"{_format_timestamp(start)} --> {_format_timestamp(end)}")
        vtt_lines.append(description)
        vtt_lines.append("")

    return "\n".join(vtt_lines)


def _format_timestamp(seconds: float) -> str:
    """Format seconds to WebVTT timestamp (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def _generate_frames_html(frames: List[Dict[str, Any]], scenes: List[Dict[str, Any]]) -> str:
    """Generate HTML for frame thumbnails timeline."""
    if not frames:
        return "<p>No frames available</p>"

    html_parts = ['<div class="timeline">']

    for i, frame_info in enumerate(frames):
        # Handle both dict and Path formats
        if isinstance(frame_info, dict):
            frame_path = Path(frame_info['path'])
            timestamp = frame_info.get('time', i * 5)
            time_str = frame_info.get('time_str', f"{int(timestamp // 60)}:{int(timestamp % 60):02d}")
        else:
            frame_path = frame_info
            timestamp = i * 5
            time_str = f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"

        if not frame_path.exists():
            continue

        # Find corresponding scene
        scene = scenes[i] if i < len(scenes) else {}
        description = scene.get("description", f"Frame {i+1}")

        # Read frame as base64
        with open(frame_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        html_parts.append(f'''
            <div class="frame-item" data-timestamp="{timestamp}">
                <img src="data:image/jpeg;base64,{img_base64}" alt="Frame {i+1}">
                <div class="frame-time">{_format_time_simple(timestamp)}</div>
                <div class="frame-desc">{description}</div>
            </div>
        ''')

    html_parts.append('</div>')
    return "\n".join(html_parts)


def _format_time_simple(seconds: float) -> str:
    """Format seconds to MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def _extract_radar_data(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract radar chart data from analysis results."""
    dimensions = analysis_data.get("dimensions", {})

    return {
        "labels": [
            "视觉冲击力",
            "信息密度",
            "节奏把控",
            "情绪调动",
            "记忆点设计",
            "完播驱动力",
            "互动引导",
            "平台适配度"
        ],
        "scores": [
            dimensions.get("visual_impact", 0),
            dimensions.get("information_density", 0),
            dimensions.get("pacing", 0),
            dimensions.get("emotional_engagement", 0),
            dimensions.get("memorable_moments", 0),
            dimensions.get("completion_drive", 0),
            dimensions.get("interaction_cues", 0),
            dimensions.get("platform_fit", 0)
        ]
    }


def _generate_html_template(
    title: str,
    analysis_data: Dict[str, Any],
    video_src: str,
    vtt_content: str,
    frames_html: str,
    radar_data: Dict[str, Any],
    is_lite: bool
) -> str:
    """Generate complete HTML template."""

    # Convert VTT to base64 data URL
    vtt_base64 = base64.b64encode(vtt_content.encode()).decode()
    vtt_url = f"data:text/vtt;base64,{vtt_base64}"

    # Extract key metrics
    overall_score = analysis_data.get("overall_score", 0)
    summary = analysis_data.get("summary", "")
    recommendations = analysis_data.get("recommendations", [])

    # Generate recommendations HTML
    recs_html = "\n".join([
        f'<li class="rec-item"><strong>{rec.get("title", "")}</strong>: {rec.get("description", "")}</li>'
        for rec in recommendations
    ])

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #1a1a2e;
            color: #eee;
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
            border-bottom: 2px solid #16213e;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #00d4ff;
        }}

        .score-badge {{
            display: inline-block;
            font-size: 3em;
            font-weight: bold;
            color: #00ff88;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 40px;
            border-radius: 15px;
            margin: 20px 0;
        }}

        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        @media (max-width: 1024px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: #16213e;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}

        .card h2 {{
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #0f3460;
            padding-bottom: 10px;
        }}

        .video-container {{
            position: relative;
            width: 100%;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
        }}

        video {{
            width: 100%;
            display: block;
        }}

        .timeline {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .frame-item {{
            cursor: pointer;
            transition: transform 0.2s;
            background: #0f3460;
            border-radius: 8px;
            overflow: hidden;
        }}

        .frame-item:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }}

        .frame-item img {{
            width: 100%;
            height: 100px;
            object-fit: cover;
            display: block;
        }}

        .frame-time {{
            padding: 5px 10px;
            background: #00d4ff;
            color: #1a1a2e;
            font-weight: bold;
            font-size: 0.9em;
            text-align: center;
        }}

        .frame-desc {{
            padding: 8px 10px;
            font-size: 0.85em;
            color: #ccc;
            min-height: 40px;
        }}

        .summary {{
            background: #0f3460;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00d4ff;
            margin-bottom: 20px;
            line-height: 1.8;
        }}

        .rec-list {{
            list-style: none;
        }}

        .rec-item {{
            background: #0f3460;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #00ff88;
        }}

        .rec-item strong {{
            color: #00ff88;
        }}

        #radarChart {{
            max-width: 500px;
            margin: 0 auto;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #888;
            border-top: 1px solid #16213e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="score-badge">{overall_score}/100</div>
        </header>

        <div class="grid">
            <div class="card full-width">
                <h2>视频预览</h2>
                <div class="video-container">
                    <video id="videoPlayer" controls>
                        <source src="{video_src}" type="video/mp4">
                        <track kind="metadata" src="{vtt_url}" default>
                        您的浏览器不支持视频播放。
                    </video>
                </div>
            </div>

            <div class="card">
                <h2>八维评分</h2>
                <canvas id="radarChart"></canvas>
            </div>

            <div class="card">
                <h2>综合评价</h2>
                <div class="summary">{summary}</div>
            </div>

            <div class="card full-width">
                <h2>优化建议</h2>
                <ul class="rec-list">
                    {recs_html}
                </ul>
            </div>

            <div class="card full-width">
                <h2>关键帧时间轴</h2>
                {frames_html}
            </div>
        </div>

        <footer>
            <p>Generated by video-optimize Skill | {"Lite Version" if is_lite else "Full Version"}</p>
        </footer>
    </div>

    <script>
        // Radar Chart
        const ctx = document.getElementById('radarChart').getContext('2d');
        new Chart(ctx, {{
            type: 'radar',
            data: {{
                labels: {json.dumps(radar_data["labels"])},
                datasets: [{{
                    label: '评分',
                    data: {json.dumps(radar_data["scores"])},
                    backgroundColor: 'rgba(0, 212, 255, 0.2)',
                    borderColor: 'rgba(0, 212, 255, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(0, 255, 136, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(0, 255, 136, 1)'
                }}]
            }},
            options: {{
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            stepSize: 20,
                            color: '#888'
                        }},
                        grid: {{
                            color: '#333'
                        }},
                        pointLabels: {{
                            color: '#eee',
                            font: {{
                                size: 12
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});

        // Frame timeline click to seek
        const video = document.getElementById('videoPlayer');
        const frames = document.querySelectorAll('.frame-item');

        frames.forEach(frame => {{
            frame.addEventListener('click', () => {{
                const timestamp = parseFloat(frame.dataset.timestamp);
                video.currentTime = timestamp;
                video.play();
            }});
        }});

        // Highlight current frame
        video.addEventListener('timeupdate', () => {{
            const currentTime = video.currentTime;
            frames.forEach(frame => {{
                const timestamp = parseFloat(frame.dataset.timestamp);
                if (Math.abs(currentTime - timestamp) < 2.5) {{
                    frame.style.border = '3px solid #00ff88';
                }} else {{
                    frame.style.border = 'none';
                }}
            }});
        }});
    </script>
</body>
</html>'''


if __name__ == "__main__":
    # Test with dummy data
    test_data = {
        "overall_score": 78,
        "summary": "视频整体质量良好，节奏把控到位，但开头3秒可以更有冲击力。",
        "dimensions": {
            "visual_impact": 75,
            "information_density": 80,
            "pacing": 85,
            "emotional_engagement": 70,
            "memorable_moments": 65,
            "completion_drive": 80,
            "interaction_cues": 60,
            "platform_fit": 75
        },
        "recommendations": [
            {"title": "开头优化", "description": "前3秒加入强视觉冲击元素"},
            {"title": "互动引导", "description": "在15秒和45秒处增加互动提示"}
        ],
        "scenes": [
            {"timestamp": 0, "end_timestamp": 5, "description": "开场介绍"},
            {"timestamp": 5, "end_timestamp": 15, "description": "核心内容展示"}
        ]
    }

    output = Path("./test_output")
    full, lite = generate_report(
        test_data,
        Path("test.mp4"),
        [],
        output,
        "测试报告"
    )
    print(f"Generated: {full}, {lite}")
