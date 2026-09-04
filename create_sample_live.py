"""動作確認用のテスト用ライブ動画をローカルで生成するスクリプト。

外部の動画ファイルを用意しなくても、ffmpegのテストソース機能を用いて
「カラーバー映像＋サイン波音」で構成されたサンプルライブ動画を即座に生成できます。
"""

import subprocess
import sys
from pathlib import Path

# Windowsのcp932エンコーディングによる文字化け・クラッシュを防止
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def create_sample_live_video(output_path: Path, duration: int = 15) -> Path:
    """指定秒数のテスト用動画（カラーバー映像＋音声）を生成する。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"テスト用サンプル動画を生成中（長さ: {duration}秒）: {output_path}")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration}:size=640x360:rate=30",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-c:a",
        "aac",
        str(output_path),
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[OK] サンプル動画の生成が完了しました！ ({output_path.stat().st_size / 1024:.1f} KB)")
    print(f"\n以下のコマンド、または drag_and_drop_cutter.bat にドラッグして動作を確認できます：")
    print(f"  python main.py \"{output_path}\" --dry-run")

    return output_path


if __name__ == "__main__":
    target = Path("./sample_live.mp4").resolve()
    create_sample_live_video(target)
