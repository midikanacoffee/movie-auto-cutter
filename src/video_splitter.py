import subprocess
from pathlib import Path
from typing import Literal

from src.models import SongSegment, sanitize_filename, seconds_to_time_str
from src.subtitle_generator import create_srt_file, export_youtube_info


def split_video(
    video_path: Path,
    segments: list[SongSegment],
    output_dir: Path,
    margin_start: float = 3.5,
    margin_end: float = 3.5,
    mc_mode: Literal["separate", "attach", "omit"] = "separate",
    reencode: bool = False,
    max_duration: float | None = None,
    generate_subtitles: bool = True,
    generate_youtube_info: bool = True,
    artist_name: str = "",
    live_title: str = "",
    recorded_date: str = "",
) -> list[Path]:
    """解析結果のセグメント情報に基づいて元動画を切り出し保存する。

    Args:
        video_path: 入力元の動画ファイルパス
        segments: 切り出すセグメントのリスト
        output_dir: 分割後ファイルの保存先ディレクトリ
        margin_start: 開始前の安全マージン秒数（頭切れ防止、デフォルト: 3.5秒）
        margin_end: 終了後の安全マージン秒数（余韻切れ防止、デフォルト: 3.5秒）
        mc_mode: MCの扱い方:
                 - "separate": MCも曲とは別の独立した動画として切り出す (デフォルト推奨)
                 - "attach": 直前のMCを曲の冒頭にくっつけて1本の動画にする
                 - "omit": MCは除外して楽曲のみを切り出す
        reencode: Trueの場合、高精度再エンコード（キーフレーム吸着ズレを完全防止）。
                  Falseの場合、無劣化ストリームコピー（数秒で終わる超高速カット）。
        max_duration: 元動画の総再生時間
        generate_subtitles: 各曲の歌詞から .srt 字幕ファイルを生成するか
        generate_youtube_info: YouTube投稿用情報テキスト (.txt) を生成するか
        artist_name: アーティスト名
        live_title: ライブタイトル
        recorded_date: ライブ開催日

    Returns:
        生成された動画ファイルパスのリスト
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    # 切り出し対象のリストを構築
    cut_tasks: list[dict] = []

    for i, seg in enumerate(segments):
        if seg.segment_type == "interval":
            continue

        if seg.segment_type == "mc":
            if mc_mode == "separate":
                adj_start, adj_end = seg.get_adjusted_range(
                    margin_start=margin_start,
                    margin_end=margin_end,
                    max_duration=max_duration,
                )
                safe_title = sanitize_filename(seg.title)
                filename = f"{seg.index:02d}_[MC]_{safe_title}.mp4"
                cut_tasks.append({
                    "segment": seg,
                    "start": adj_start,
                    "end": adj_end,
                    "filename": filename,
                    "is_mc": True,
                })
            # attach の場合は song の処理時に結合されるためここではスキップ

        elif seg.segment_type == "song":
            start_sec = seg.start_seconds
            safe_title = sanitize_filename(seg.title)
            filename = f"{seg.index:02d}_{safe_title}.mp4"

            # attach モードで直前のセグメントがMCの場合、そのMCの開始から切り出す
            if mc_mode == "attach" and i > 0 and segments[i - 1].segment_type == "mc":
                prev_mc = segments[i - 1]
                start_sec = prev_mc.start_seconds
                filename = f"{seg.index:02d}_[MC+Song]_{safe_title}.mp4"

            adj_start = max(0.0, start_sec - margin_start)
            adj_end = seg.end_seconds + margin_end
            if max_duration is not None:
                adj_end = min(max_duration, adj_end)

            cut_tasks.append({
                "segment": seg,
                "start": adj_start,
                "end": adj_end,
                "filename": filename,
                "is_mc": False,
            })

    total = len(cut_tasks)
    print(f"\n合計 {total} 件の動画を切り出します（出力先: {output_dir}）")

    for i, task in enumerate(cut_tasks, start=1):
        seg = task["segment"]
        adj_start = task["start"]
        adj_end = task["end"]
        filename = task["filename"]
        output_path = output_dir / filename

        start_str = seconds_to_time_str(adj_start)
        end_str = seconds_to_time_str(adj_end)
        duration_sec = max(0.1, adj_end - adj_start)

        print(
            f"[{i}/{total}] 切り出し中: {filename} "
            f"({start_str} 〜 {end_str}, 長さ: {duration_sec:.1f}秒)"
        )

        if reencode:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{adj_start:.3f}",
                "-to",
                f"{adj_end:.3f}",
                "-i",
                str(video_path),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(output_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{adj_start:.3f}",
                "-to",
                f"{adj_end:.3f}",
                "-i",
                str(video_path),
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                str(output_path),
            ]

        try:
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            generated_files.append(output_path)

            # 字幕ファイル (.srt) の出力
            if generate_subtitles and (seg.lyrics or seg.notes):
                srt_path = output_path.with_suffix(".srt")
                lyrics_text = seg.lyrics if seg.lyrics else seg.notes
                create_srt_file(srt_path, lyrics_text, duration_sec)

            # YouTube投稿用メタデータ (.txt) の出力
            if generate_youtube_info and not task["is_mc"]:
                info_path = output_dir / f"{output_path.stem}_youtube_info.txt"
                export_youtube_info(
                    info_path,
                    segment=seg,
                    artist_name=artist_name,
                    live_title=live_title,
                    recorded_date=recorded_date,
                )

        except subprocess.CalledProcessError as e:
            print(f"  [エラー] {filename} の切り出しに失敗しました: {e.stderr.decode('utf-8', errors='ignore')}")

    print(f"\nすべての切り出し処理が完了しました！（動画ファイル: {len(generated_files)}件）")
    return generated_files
