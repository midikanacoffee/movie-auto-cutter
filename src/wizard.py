"""対話型CLIセットアップウィザードモジュール。

ユーザーがコマンドラインオプションを覚えなくても、
画面の質問にEnterを押すだけで最適な設定で動画分割を実行できます。
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class WizardConfig:
    mc_mode: Literal["separate", "attach", "omit"] = "separate"
    margin_start: float = 3.5
    margin_end: float = 3.5
    generate_subtitles: bool = True
    generate_youtube_info: bool = True
    reencode: bool = False


def run_interactive_wizard(video_name: str) -> WizardConfig:
    """対話形式でユーザーに切り出し設定を問い合わせるウィザード。

    Enterキーを押すだけで推奨（デフォルト）値が自動選択されます。
    """
    print("\n" + "=" * 62)
    print("🎬 Live Movie Auto Cutter - 切り出し設定ウィザード")
    print(f"対象動画: {video_name}")
    print("（※各質問は、何も入力せず [Enter] を押すと推奨値が選ばれます）")
    print("=" * 62 + "\n")

    config = WizardConfig()

    # 1. MCの扱い
    print("【1/4】MC（トーク）の扱いを選択してください:")
    print("  [1] MCも別ファイルとして個別に保存する (推奨: [MC]_タイトル.mp4)")
    print("  [2] MCを直後の曲の冒頭に結合して1本の動画にする ([MC+Song]_タイトル.mp4)")
    print("  [3] MCは除外する（楽曲のみ切り出し）")
    choice_mc = input("選択 [1-3] (デフォルト: 1): ").strip()
    if choice_mc == "2":
        config.mc_mode = "attach"
    elif choice_mc == "3":
        config.mc_mode = "omit"
    else:
        config.mc_mode = "separate"
    print(f"  → 選択: {config.mc_mode}\n")

    # 2. 安全マージン
    print("【2/4】曲前後の安全マージン（余白）を選択してください:")
    print("  [1] 標準 (前後 3.5秒) - 余裕をもった切り出し (推奨)")
    print("  [2] 広め (前後 5.0秒) - 歓声や会場の雰囲気を多めに残す")
    print("  [3] 狭め (前後 2.0秒) - タイトに切る")
    print("  [4] カスタム秒数を手動入力")
    choice_margin = input("選択 [1-4] (デフォルト: 1): ").strip()
    if choice_margin == "2":
        config.margin_start = 5.0
        config.margin_end = 5.0
    elif choice_margin == "3":
        config.margin_start = 2.0
        config.margin_end = 2.0
    elif choice_margin == "4":
        custom_val = input("前後の秒数を入力してください (例: 4.0): ").strip()
        try:
            val = float(custom_val)
            config.margin_start = val
            config.margin_end = val
        except ValueError:
            print("  ! 数値が無効だったため、標準 3.5秒 を適用します。")
            config.margin_start = 3.5
            config.margin_end = 3.5
    else:
        config.margin_start = 3.5
        config.margin_end = 3.5
    print(f"  → 選択: 前後 {config.margin_start:.1f} 秒\n")

    # 3. 歌詞字幕 (.srt) と YouTube投稿用情報 (.txt)
    print("【3/4】歌詞字幕 (.srt) と YouTube投稿用情報 (.txt) を出力しますか？")
    print("  [1] 出力する (推奨 - 各曲の字幕と概要欄用テキストを自動生成)")
    print("  [2] 出力しない")
    choice_sub = input("選択 [1-2] (デフォルト: 1): ").strip()
    if choice_sub == "2":
        config.generate_subtitles = False
        config.generate_youtube_info = False
        print("  → 選択: 出力しない\n")
    else:
        config.generate_subtitles = True
        config.generate_youtube_info = True
        print("  → 選択: 出力する\n")

    # 4. 切り出し方式（無劣化 or 高精度再エンコード）
    print("【4/4】動画の切り出し方式を選択してください:")
    print("  [1] 高速・無劣化カット (数秒で完了・画質劣化ゼロ) (推奨)")
    print("  [2] 高精度再エンコード (秒数通りの完全フレーム精度・少し時間がかかります)")
    choice_enc = input("選択 [1-2] (デフォルト: 1): ").strip()
    if choice_enc == "2":
        config.reencode = True
        print("  → 選択: 高精度再エンコード\n")
    else:
        config.reencode = False
        print("  → 選択: 高速・無劣化カット\n")

    print("=" * 62)
    print("✓ 設定完了！動画の解析と分割処理を開始します...")
    print("=" * 62 + "\n")

    return config
