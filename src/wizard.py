"""対話型CLIセットアップウィザードモジュール。

ユーザーがコマンドラインオプションを覚えなくても、
画面の質問にEnterを押すだけで最適な設定で動画分割を実行できます。
"""

from dataclasses import dataclass, field
from typing import Literal

from src.models import VideoEffectsConfig


@dataclass
class WizardConfig:
    mc_mode: Literal["separate", "attach", "omit"] = "separate"
    margin_start: float = 3.5
    margin_end: float = 3.5
    include_opening: bool = True
    include_ending: bool = True
    generate_subtitles: bool = False
    generate_youtube_info: bool = True
    reencode: bool = False
    effects_config: VideoEffectsConfig = field(default_factory=VideoEffectsConfig)


def run_interactive_wizard(video_name: str) -> WizardConfig:
    """対話形式でユーザーに切り出し設定を問い合わせるウィザード。

    Enterキーを押すだけで推奨（デフォルト）値が自動選択されます。
    """
    print("\n" + "=" * 64)
    print("🎬 Live Movie Auto Cutter - 切り出し設定ウィザード")
    print(f"対象動画: {video_name}")
    print("（※各質問は、何も入力せず [Enter] を押すと推奨値が選ばれます）")
    print("=" * 64 + "\n")

    config = WizardConfig()

    # 1. MCの扱い
    print("【1/5】MC（トーク）の扱いを選択してください:")
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

    # 2. オープニングとエンディング
    print("【2/5】オープニング（開演前）とエンディング（終演後）も別で切り出しますか？")
    print("  [1] 切り出す (推奨: 00_[Opening]_...mp4 / 99_[Ending]_...mp4)")
    print("  [2] 切り出さない")
    choice_oe = input("選択 [1-2] (デフォルト: 1): ").strip()
    if choice_oe == "2":
        config.include_opening = False
        config.include_ending = False
        print("  → 選択: 切り出さない\n")
    else:
        config.include_opening = True
        config.include_ending = True
        print("  → 選択: オープニング・エンディングも切り出す\n")

    # 3. 安全マージン
    print("【3/5】曲前後の安全マージン（余白）を選択してください:")
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

    # 4. 動画演出（テロップ・フェード・終了メッセージ）
    print("【4/5】曲動画に演出（フェードイン/アウト・曲名テロップ・終了メッセージ）を付けますか？")
    print("  [1] つけない (推奨: 超高速・無劣化カット、画質劣化ゼロで数秒で完了)")
    print("  [2] つける (YouTube向け演出: フェードイン/アウト・曲名テロップ・「ご視聴ありがとうございました」を自動合成)")
    choice_fx = input("選択 [1-2] (デフォルト: 1): ").strip()

    if choice_fx == "2":
        print("  → 演出オプションを有効にします。")
        config.effects_config.enable_fade = True
        config.effects_config.enable_title_overlay = True
        config.effects_config.enable_closing_message = True

        # テロップ位置の選択
        print("\n  曲名・アーティスト名テロップの表示位置を選択してください:")
        print("    [1] 左下 (推奨 - 音楽番組風)")
        print("    [2] 右下")
        print("    [3] 左上")
        print("    [4] 右上")
        choice_pos = input("  選択 [1-4] (デフォルト: 1): ").strip()
        pos_map = {
            "2": "bottom_right",
            "3": "top_left",
            "4": "top_right",
        }
        config.effects_config.overlay_position = pos_map.get(choice_pos, "bottom_left")
        print(f"  → テロップ位置: {config.effects_config.overlay_position}\n")
    else:
        print("  → 選択: 演出なし（高速・無劣化カット）\n")

    # 5. YouTube投稿用テキスト (.txt) の出力
    print("【5/5】YouTube投稿用情報テキスト (.txt) を自動出力しますか？")
    print("  [1] 出力する (推奨 - 各曲のタイトル・概要欄コピペ用テキストを自動生成)")
    print("  [2] 出力しない")
    choice_yt = input("選択 [1-2] (デフォルト: 1): ").strip()
    if choice_yt == "2":
        config.generate_youtube_info = False
        print("  → 選択: 出力しない\n")
    else:
        config.generate_youtube_info = True
        print("  → 選択: 出力する\n")

    print("=" * 64)
    print("✓ 設定完了！動画の解析と分割処理を開始します...")
    print("=" * 64 + "\n")

    return config
