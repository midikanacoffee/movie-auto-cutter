# タスクリスト: ライブ動画 自動曲間認識・分割ツール

## フェーズ 1: セキュリティ・リポジトリ初期設定
- [x] セキュリティ対応設定ファイルの作成 (`.gitignore`, `.env.example`, `README.md`)
- [x] Gitリポジトリ初期化 (`git init`)
- [x] GitHubプライベートリポジトリの作成・リモート連携
- [x] 初期コミット (`main` ブランチ)

## フェーズ 2: ブランチ作成・環境構築
- [x] トピックブランチ作成 (`feature/live-splitter`)
- [x] 必要な依存パッケージの確認 (既存環境で充足、追加不要)

## フェーズ 3: コア機能実装
- [x] 音声抽出モジュール (`src/audio_extractor.py`) の実装
- [x] Gemini API連携・解析モジュール (`src/gemini_analyzer.py`) の実装
  - 安全マージン処理
  - フォールバック命名処理
  - JSON構造化出力
  - Files API解析後の自動クリーンアップ
- [x] 動画分割・リネームモジュール (`src/video_splitter.py`) の実装
- [x] CLIエントリーポイント (`main.py`) の実装
- [x] ドラッグ＆ドロップ用バッチ (`drag_and_drop_cutter.bat`) の実装

## フェーズ 4: 動作検証・テスト
- [x] 単体テスト (`tests/test_models.py`) の実行
- [x] ffmpegダミー動画による結合動作テスト (`tests/test_e2e_split.py`)
- [x] セキュリティ最終チェック (リポジトリ内にAPIキーやメディアファイルが含まれていないかの確認)

## フェーズ 5: PR作成・マージ・完了
- [x] トピックブランチへのコミット
- [ ] プルリクエスト (PR) の作成
- [ ] メインブランチへのマージ
- [x] 完了報告 (`walkthrough.md`) の作成
