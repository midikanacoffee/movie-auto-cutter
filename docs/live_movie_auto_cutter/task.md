# タスクリスト: ライブ動画 自動曲間認識・分割ツール

## フェーズ 1: セキュリティ・リポジトリ初期設定
- [x] セキュリティ対応設定ファイルの作成 (`.gitignore`, `.env.example`, `README.md`)
- [x] Gitリポジトリ初期化 (`git init`)
- [x] GitHubプライベートリポジトリの作成・リモート連携
- [x] 初期コミット (`main` ブランチ)

## フェーズ 2: ブランチ作成・環境構築
- [x] トピックブランチ作成 (`feature/live-splitter`)
- [x] 必要な依存パッケージの確認 (既存環境で充足、追加不要)
- [x] Gemini APIキーのローカル設定・疎通確認 (gemini-3.8-flash 接続成功)

## フェーズ 3: コア機能実装
- [x] 音声抽出モジュール (`src/audio_extractor.py`) の実装
- [x] Gemini API連携・解析モジュール (`src/gemini_analyzer.py`) の実装
  - 安全マージン処理 (前後3.5秒)
  - フォールバック命名処理
  - JSON構造化出力
  - Files API解析後の自動クリーンアップ
  - 503/429高負荷時の自動リトライ＆フォールバック
  - 日本語等の非ASCIIファイル名安全アップロード対応
  - 歌詞・YouTubeメタデータ（タイトル・概要欄・雰囲気・日時・タグ）抽出対応
- [x] 動画分割・リネームモジュール (`src/video_splitter.py`) の実装
  - MC個別切り出し (`separate`)
  - 直前MCの楽曲冒頭への結合切り出し (`attach`)
  - 歌詞SRT字幕およびYouTube投稿用テキスト出力
- [x] 対話型ウィザード (`src/wizard.py`) の実装
- [x] 字幕SRT・YouTubeテキスト生成 (`src/subtitle_generator.py`) の実装
- [x] エラーログ出力モジュール (`src/logger.py`) の実装 (`logs/app.log`)
- [x] CLIエントリーポイント (`main.py`) の実装 (Windows UTF-8対応、ウィザード連携)
- [x] ドラッグ＆ドロップ用バッチ (`drag_and_drop_cutter.bat`) の実装

## フェーズ 4: 動作検証・テスト
- [x] 単体テスト (`tests/test_models.py`, `tests/test_subtitle_generator.py`) の実行
- [x] ffmpegダミー動画による結合動作テスト (`tests/test_e2e_split.py`)
- [x] 日本語ファイル名およびロギングテスト (`tests/test_japanese_filename.py`)
- [x] サンプル動画生成ツール (`create_sample_live.py`) の追加と実地API解析テスト
- [x] セキュリティ最終チェック (リポジトリ内にAPIキーやメディアファイルが含まれていないかの確認)

## フェーズ 5: ドキュメント拡充 & PRマージ
- [x] README.mdの最新仕様・全オプション表・ウィザード・出力先詳細の全面改訂
- [x] システム詳細設計書 & ADR (`docs/live_movie_auto_cutter/architecture.md`) の作成
- [x] トラブルシューティング & FAQ (`docs/live_movie_auto_cutter/troubleshooting.md`) の作成
- [x] Antigravity全体スキル (`proactive-development-standards`) の登録
- [x] 全プルリクエスト (PR #1 〜 #6) の作成および main へのマージ完了

## フェーズ 6: オープニング/エンディング・動画演出（フェード・テロップ）
- [x] 4区分セグメンテーション（Opening/Song/MC/Ending）の判定・モデル定義 (`src/models.py`, `src/gemini_analyzer.py`)
- [x] 歌詞幻覚の抑制プロンプト強化（聞き取れない場合は空文字）
- [x] 動画演出フィルタ生成モジュール (`src/video_effects.py`) の新規実装
  - 冒頭フェードイン・末尾フェードアウト（映像・音声）
  - Windows日本語フォント（Meiryo）自動検出
  - 曲名・アーティスト名テロップ（四隅指定: 左下/右下/左上/右上、半透明ボックス付き）
  - 動画末尾メッセージ（「ご視聴ありがとうございました」等）
- [x] 動画切り出しモジュール (`src/video_splitter.py`) の演出ハイブリッド適用とOpening/Ending命名 (`00_[Opening]_...mp4`, `99_[Ending]_...mp4`)
- [x] 対話型ウィザード (`src/wizard.py`) へのオープニング/エンディングおよび演出・テロップ位置の質問追加
- [x] 単体テスト & E2E演出テスト追加 (`tests/test_video_effects.py`, `tests/test_e2e_split.py`) (全16件 PASS)
- [x] ドキュメント同期更新 (`README.md`, `docs/live_movie_auto_cutter/architecture.md` ADR-07, `docs/live_movie_auto_cutter/troubleshooting.md` Q10-Q13)

## フェーズ 7: Public（公開）リポジトリ対応準備
- [x] 機密情報・APIキー・個人パスの全Git履歴精密スキャン（完全安全を確認）
- [x] 外部依存ライブラリ一覧 (`requirements.txt`) の作成
- [x] オープンソースライセンスファイル (`LICENSE`: MIT License) の作成
- [x] `README.md` のセットアップ手順更新 (`pip install -r requirements.txt`) およびライセンス表記追加

