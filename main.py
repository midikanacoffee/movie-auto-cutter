import argparse
import hashlib
import json
import sys
from pathlib import Path

# Windows環境での文字化けおよびUnicodeEncodeErrorを防止
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.audio_extractor import extract_audio, get_video_duration
from src.gemini_analyzer import analyze_live_audio
from src.logger import setup_logger
from src.models import LiveAnalysisResult
from src.video_splitter import split_video


def print_summary_table(result: LiveAnalysisResult) -> None:
    """解析結果のセットリストを見やすく表示する。"""
    print("\n" + "=" * 60)
    print(f"🎵 ライブ解析結果: {result.live_title or 'ライブ音源'}")
    if result.artist_name:
        print(f"🎤 アーティスト: {result.artist_name}")
    print("=" * 60)
    print(f"{'No':<4} | {'種類':<6} | {'時間':<17} | {'曲名 / 内容'}")
    print("-" * 60)

    type_labels = {
        "song": "楽曲",
        "mc": "MC",
        "interval": "待機",
    }

    for seg in result.segments:
        label = type_labels.get(seg.segment_type, seg.segment_type)
        time_range = f"{seg.start_time} - {seg.end_time}"
        print(f"{seg.index:<4} | {label:<6} | {time_range:<17} | {seg.title}")
        if seg.notes:
            print(f"     └ メモ: {seg.notes}")

    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ライブ動画からAIで曲間と曲名を自動認識し、曲ごとに動画を分割するツール",
    )
    parser.add_argument(
        "video_path",
        type=str,
        help="対象のライブ動画ファイルパス (.mp4, .mkv, .mov等)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="分割動画の保存先フォルダ（デフォルト: ./output/<動画名>/）",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        default=None,
        help="すでに解析済みのセットリストJSONファイルを使って動画分割のみ実行する場合に指定",
    )
    parser.add_argument(
        "--margin-start",
        type=float,
        default=2.0,
        help="曲開始前の安全マージン秒数（頭切れ防止、デフォルト: 2.0秒）",
    )
    parser.add_argument(
        "--margin-end",
        type=float,
        default=2.0,
        help="曲終了後の安全マージン秒数（余韻切れ防止、デフォルト: 2.0秒）",
    )
    parser.add_argument(
        "--include-mc",
        action="store_true",
        help="MC区間も動画として切り出す場合に指定（デフォルトは楽曲のみ）",
    )
    parser.add_argument(
        "--reencode",
        action="store_true",
        help="高精度再エンコードモードで切り出す（キーフレームずれを防ぎたい場合）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="動画の分割は行わず、セットリスト解析とJSON保存のみ行う",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.8-flash",
        help="使用するGeminiモデル名（デフォルト: gemini-3.8-flash）",
    )

    args = parser.parse_args()
    video_path = Path(args.video_path).resolve()

    if not video_path.exists():
        print(f"[エラー] 指定された動画ファイルが見つかりません: {video_path}", file=sys.stderr)
        sys.exit(1)

    logger = setup_logger()

    video_stem = video_path.stem
    output_dir = Path(args.output_dir) if args.output_dir else Path("./output") / video_stem
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    max_duration = get_video_duration(video_path)

    try:
        # 1. 解析データの取得（JSONからの復元、またはGemini API解析）
        if args.from_json:
            json_path = Path(args.from_json).resolve()
            logger.info(f"既存の解析データから読み込み中: {json_path}")
            with open(json_path, "r", encoding="utf-8") as f:
                analysis_data = json.load(f)
            analysis_result = LiveAnalysisResult.model_validate(analysis_data)
        else:
            temp_dir = Path("./temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 日本語や記号を含む動画名でも安全にAPIアップロードできるよう、ハッシュを用いたASCIIファイル名にする
            safe_hash = hashlib.md5(video_path.name.encode("utf-8")).hexdigest()[:10]
            temp_audio_path = temp_dir / f"extracted_{safe_hash}.mp3"

            try:
                logger.info(f"\n[ステップ 1/3] 動画から音声を抽出中...")
                extract_audio(video_path, temp_audio_path, bitrate="96k")
                logger.info(f"  ✓ 音声抽出完了: {temp_audio_path.name} ({temp_audio_path.stat().st_size / (1024*1024):.1f} MB)")

                logger.info(f"\n[ステップ 2/3] Gemini API ({args.model}) でセットリスト・曲間を解析中...")
                analysis_result = analyze_live_audio(temp_audio_path, model_name=args.model)

                # 解析結果のJSONを保存（ユーザーが確認・微調整できるように）
                saved_json_path = output_dir / "setlist.json"
                with open(saved_json_path, "w", encoding="utf-8") as f:
                    f.write(analysis_result.model_dump_json(indent=2))
                logger.info(f"  ✓ 解析結果を保存しました: {saved_json_path}")

            finally:
                # 一時音声ファイルのクリーンアップ
                if temp_audio_path.exists():
                    try:
                        temp_audio_path.unlink()
                    except Exception:
                        pass

        # 2. 結果サマリーの表示
        print_summary_table(analysis_result)

        if args.dry_run:
            logger.info("💡 --dry-run が指定されているため、動画の分割はスキップしました。")
            logger.info(f"   タイムスタンプを微調整したい場合は、{output_dir / 'setlist.json'} を編集した上で、")
            logger.info(f"   python main.py \"{video_path}\" --from-json \"{output_dir / 'setlist.json'}\" を実行してください。")
            return

        # 3. 動画の分割実行
        logger.info(f"[ステップ 3/3] 動画の分割切り出しを開始します...")
        split_video(
            video_path=video_path,
            segments=analysis_result.segments,
            output_dir=output_dir,
            margin_start=args.margin_start,
            margin_end=args.margin_end,
            include_mc=args.include_mc,
            reencode=args.reencode,
            max_duration=max_duration if max_duration > 0 else None,
        )

    except Exception as e:
        logger.exception("処理中にエラーが発生しました: %s", e)
        print(f"\n[エラー] 処理が中断されました: {e}", file=sys.stderr)
        print("詳細なエラーログは 'logs/app.log' に記録されています。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
