import json
import subprocess
from pathlib import Path


def get_video_duration(video_path: Path) -> float:
    """ffprobeを使用して動画の総再生時間（秒）を取得する。"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio(
    video_path: Path,
    output_audio_path: Path,
    bitrate: str = "96k",
) -> Path:
    """動画から音声のみを軽量なMP3として抽出する。

    動画ファイル全体をAPIに送ると大容量になりアップロードに時間がかかるため、
    軽量な音声（デフォルト96kbps）に変換して高速転送・APIコスト削減を実現します。

    Args:
        video_path: 入力動画ファイルのパス
        output_audio_path: 出力先音声ファイルのパス (.mp3)
        bitrate: 音声ビットレート (例: "96k", "128k")

    Returns:
        抽出された音声ファイルのパス
    """
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        bitrate,
        "-ar",
        "44100",
        str(output_audio_path),
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    return output_audio_path
