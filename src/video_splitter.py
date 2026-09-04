import subprocess
from pathlib import Path
from src.models import SongSegment, sanitize_filename, seconds_to_time_str


def split_video(
    video_path: Path,
    segments: list[SongSegment],
    output_dir: Path,
    margin_start: float = 2.0,
    margin_end: float = 2.0,
    include_mc: bool = False,
    reencode: bool = False,
    max_duration: float | None = None,
) -> list[Path]:
    """解析結果のセグメント情報に基づいて元動画を切り出し保存する。

    Args:
        video_path: 入力元の動画ファイルパス
        segments: 切り出すセグメントのリスト
        output_dir: 分割後ファイルの保存先ディレクトリ
        margin_start: 開始前の安全マージン秒数（頭切れ防止）
        margin_end: 終了後の安全マージン秒数（余韻切れ防止）
        include_mc: MC区間も切り出して保存するかどうか
        reencode: Trueの場合、高精度再エンコード（キーフレーム吸着ズレを完全防止）。
                  Falseの場合、無劣化ストリームコピー（数秒で終わる超高速カット）。
        max_duration: 元動画の総再生時間（マージンが動画終端を超えないよう制限）

    Returns:
        生成された動画ファイルパスのリスト
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    target_segments = [
        s for s in segments
        if s.segment_type == "song" or (include_mc and s.segment_type == "mc")
    ]

    total = len(target_segments)
    print(f"\n合計 {total} 件の区間を切り出します（出力先: {output_dir}）")

    for i, seg in enumerate(target_segments, start=1):
        adj_start, adj_end = seg.get_adjusted_range(
            margin_start=margin_start,
            margin_end=margin_end,
            max_duration=max_duration,
        )

        safe_title = sanitize_filename(seg.title)
        prefix = f"{seg.index:02d}"
        if seg.segment_type == "mc":
            filename = f"{prefix}_[MC]_{safe_title}.mp4"
        else:
            filename = f"{prefix}_{safe_title}.mp4"

        output_path = output_dir / filename

        start_str = seconds_to_time_str(adj_start)
        end_str = seconds_to_time_str(adj_end)
        duration_sec = max(0.1, adj_end - adj_start)

        print(
            f"[{i}/{total}] 切り出し中: {filename} "
            f"({start_str} 〜 {end_str}, 長さ: {duration_sec:.1f}秒)"
        )

        if reencode:
            # 高精度再エンコード（指定した秒数通りに1フレーム単位で綺麗に切る）
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
            # 無劣化ストリームコピー（超高速、再エンコードなし）
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
        except subprocess.CalledProcessError as e:
            print(f"  [エラー] {filename} の切り出しに失敗しました: {e.stderr.decode('utf-8', errors='ignore')}")

    print(f"\nすべての切り出し処理が完了しました！（生成ファイル数: {len(generated_files)}）")
    return generated_files
