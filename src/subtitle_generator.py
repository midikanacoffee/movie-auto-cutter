"""字幕ファイル（.srt）およびYouTube投稿用テキスト（_youtube_info.txt）を生成するモジュール。
"""

from pathlib import Path
from src.models import SongSegment


def format_srt_time(seconds: float) -> str:
    """秒数を SRT 形式のタイムコード (HH:MM:SS,mmm) に変換する。"""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def create_srt_file(
    output_path: Path,
    lyrics_or_text: str,
    duration_sec: float,
) -> Path | None:
    """歌詞テキストから動画再生プレーヤーやYouTubeで利用できる .srt 字幕ファイルを生成する。

    Args:
        output_path: 出力先 .srt ファイルパス
        lyrics_or_text: 歌詞やMCのテキスト
        duration_sec: 切り出された動画の総秒数

    Returns:
        生成された字幕ファイルのパス（歌詞が空の場合はNone）
    """
    text = lyrics_or_text.strip()
    if not text:
        return None

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    # 各行の表示時間を動画の長さに合わせて均等に配分（最低2秒、最大8秒）
    total_lines = len(lines)
    interval = max(2.0, min(8.0, duration_sec / max(1, total_lines)))

    srt_entries: list[str] = []
    current_time = 1.0  # 開始1秒後から表示

    for i, line in enumerate(lines, start=1):
        if current_time >= duration_sec:
            break
        end_time = min(duration_sec - 0.5, current_time + interval)
        start_str = format_srt_time(current_time)
        end_str = format_srt_time(end_time)

        srt_entries.append(f"{i}\n{start_str} --> {end_str}\n{line}\n")
        current_time = end_time + 0.5

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(srt_entries), encoding="utf-8")
    return output_path


def export_youtube_info(
    output_path: Path,
    segment: SongSegment,
    artist_name: str = "",
    live_title: str = "",
    recorded_date: str = "",
) -> Path:
    """YouTube投稿時にコピペしてすぐ使えるメタデータテキスト（タイトル・概要欄・タグ等）を出力する。"""
    meta = segment.youtube_metadata

    title = meta.title if meta and meta.title else f"【Live】{segment.title} - {artist_name or 'Live'}"
    description = meta.description if meta and meta.description else segment.notes or "ライブ映像の切り出しです。"
    mood = meta.mood_and_atmosphere if meta and meta.mood_and_atmosphere else "エネルギッシュなライブ演奏"
    date_str = meta.recorded_date if meta and meta.recorded_date else recorded_date
    tags_str = ", ".join(meta.tags) if meta and meta.tags else "Live, ライブ, 音楽"

    content = f"""================================================================================
📺 YouTube 投稿用情報: {segment.title}
================================================================================

【動画タイトル (コピペ用)】
{title}

--------------------------------------------------------------------------------
【概要欄 / 説明文 (コピペ用)】
{description}

【楽曲・演奏の雰囲気】
{mood}
"""
    if date_str:
        content += f"\n【収録日 / ライブ日時】\n{date_str}\n"

    if segment.lyrics:
        content += f"\n【歌詞】\n{segment.lyrics}\n"

    content += f"""--------------------------------------------------------------------------------
【おすすめタグ】
{tags_str}

================================================================================
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
