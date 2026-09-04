"""動画の演出（フェードイン/アウト、曲名テロップ、エンディングメッセージ）を行うffmpegフィルタ生成モジュール。
"""

import sys
from pathlib import Path
from src.models import VideoEffectsConfig


def get_system_fontfile() -> str:
    """Windows環境で利用可能な日本語TrueType/OpenTypeフォントのパスを取得する。"""
    if sys.platform == "win32":
        candidates = [
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/yumin.ttf",
        ]
        for c in candidates:
            if Path(c).exists():
                # ffmpeg drawtext では Windowsパスのコロンをエスケープする必要がある (C\:/Windows/...)
                return c.replace(":", "\\:")
    return ""


def escape_ffmpeg_text(text: str) -> str:
    """ffmpeg drawtext フィルタ用に特殊文字をエスケープする。"""
    # バックスラッシュ、コロン、パーセント、シングルクォートをエスケープ
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    text = text.replace("'", "'\\''")
    return text


def build_filtergraph(
    config: VideoEffectsConfig,
    song_title: str,
    artist_name: str,
    duration_sec: float,
) -> tuple[str, str]:
    """VideoEffectsConfig に基づいて ffmpeg の -vf (ビデオ) および -af (オーディオ) フィルタ文字列を生成する。

    Returns:
        tuple[str, str]: (video_filter, audio_filter)
    """
    vf_parts: list[str] = []
    af_parts: list[str] = []

    fontfile = get_system_fontfile()
    font_param = f"fontfile='{fontfile}':" if fontfile else ""

    # 1. 冒頭フェードイン & 末尾フェードアウト
    if config.enable_fade and duration_sec > (config.fade_duration * 2):
        fade_d = config.fade_duration
        out_start = max(0.0, duration_sec - fade_d)
        vf_parts.append(f"fade=t=in:st=0:d={fade_d:.2f}")
        vf_parts.append(f"fade=t=out:st={out_start:.2f}:d={fade_d:.2f}")

        af_parts.append(f"afade=t=in:st=0:d={fade_d:.2f}")
        af_parts.append(f"afade=t=out:st={out_start:.2f}:d={fade_d:.2f}")

    # 2. 曲名・アーティスト名テロップ (drawtext)
    if config.enable_title_overlay and song_title:
        title_escaped = escape_ffmpeg_text(song_title)
        artist_escaped = escape_ffmpeg_text(artist_name) if artist_name else ""

        if artist_escaped:
            display_text = f"♪ {title_escaped}\\n   {artist_escaped}"
        else:
            display_text = f"♪ {title_escaped}"

        # 表示位置
        pos_map = {
            "bottom_left": "x=40:y=h-th-40",
            "bottom_right": "x=w-tw-40:y=h-th-40",
            "top_left": "x=40:y=40",
            "top_right": "x=w-tw-40:y=40",
        }
        pos_expr = pos_map.get(config.overlay_position, "x=40:y=h-th-40")

        # 表示タイミング
        start_t = config.overlay_start_sec
        end_t = min(duration_sec - 1.0, start_t + config.overlay_duration)

        if end_t > start_t:
            drawtext_cmd = (
                f"drawtext={font_param}text='{display_text}':"
                f"fontsize=26:fontcolor=white:"
                f"box=1:boxcolor=black@0.6:boxborderw=10:"
                f"{pos_expr}:enable='between(t\\,{start_t:.2f}\\,{end_t:.2f})'"
            )
            vf_parts.append(drawtext_cmd)

    # 3. エンディングメッセージ (動画末尾のメッセージ)
    if config.enable_closing_message and config.closing_message and duration_sec >= 4.0:
        msg_escaped = escape_ffmpeg_text(config.closing_message)
        msg_start = max(0.0, duration_sec - 4.0)
        msg_end = max(msg_start, duration_sec - 0.5)

        closing_cmd = (
            f"drawtext={font_param}text='{msg_escaped}':"
            f"fontsize=32:fontcolor=white:"
            f"box=1:boxcolor=black@0.7:boxborderw=12:"
            f"x=(w-tw)/2:y=h-th-60:enable='between(t\\,{msg_start:.2f}\\,{msg_end:.2f})'"
        )
        vf_parts.append(closing_cmd)

    vf_str = ",".join(vf_parts)
    af_str = ",".join(af_parts)
    return vf_str, af_str
