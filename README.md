# Live Movie Auto Cutter (ライブ動画 自動曲間認識・分割ツール)

ライブ動画（MP4等）から音声を抽出し、最新の **Gemini 3.8 Flash** を用いて各楽曲の境界（開始・終了時間）と曲名を自動特定した上で、ffmpegを用いて曲ごとに自動分割・自動命名して保存するローカル完結型ツールです。

---

## 主な特徴

- **最新AIによる高精度曲間認識**: 最新の `gemini-3.8-flash` モデルにより、演奏、MC、客席歓声、アンコール待ちを自動判別。
- **超高速・無劣化カット**: ffmpegのストリームコピー（`-c copy`）により、画質劣化ゼロ・数秒での高速分割を実現。
- **安全マージン機能**: 曲頭・曲末の切れを防ぐため、開始前2.0秒・終了後2.0秒（秒数調整可能）の安全マージンを自動付与。
- **フォールバック自動命名**: 曲名が分からない未知の楽曲でも、歌詞や演奏の特徴から「`01_Track_01_歌詞フレーズ.mp4`」などの識別しやすいファイル名を自動命名。
- **手動微調整モード**: `--dry-run` でセットリストJSONのみを出力し、秒数や曲名を手動編集してから切り出す柔軟なフローをサポート。
- **徹底したセキュリティ・プライバシー保護**: APIキー（`.env`）や動画・音声データは `.gitignore` により完全隔離。クラウド側の解析用一時音声も処理完了後に即時削除。

---

## 必要要件

- **OS**: Windows / macOS / Linux
- **Python**: 3.10 以上
- **ffmpeg**: システム環境変数 `PATH` に通っていること
- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey) より無料で取得可能

---

## セットアップ

1. 設定用テンプレート `.env.example` をコピーして `.env` を作成します：
   ```bash
   cp .env.example .env
   ```
2. `.env` ファイルを開き、取得したGemini APIキーを設定してください：
   ```env
   GEMINI_API_KEY=ここにAPIキーを記述
   ```
   > [!NOTE]
   > `.env` ファイルは `.gitignore` により厳重に保護されているため、Gitにコミットされることはありません。

---

## 使い方

### 方法 1: ドラッグ＆ドロップ（最も手軽）
動画ファイル（`.mp4`, `.mkv`, `.mov` 等）を、プロジェクトフォルダ内にある **`drag_and_drop_cutter.bat`** にドラッグ＆ドロップするだけで、自動で音声抽出から曲ごとの分割まで完了します。

### 方法 2: コマンドライン実行
ターミナル（PowerShell等）から、各種オプションを指定して柔軟に実行できます：

```powershell
# 基本実行（楽曲ごとに自動分割）
python main.py "path/to/live.mp4"

# 出力先フォルダを指定する場合
python main.py "path/to/live.mp4" -o "D:\MyLiveVideos\Songs"

# MC区間も動画として切り出したい場合
python main.py "path/to/live.mp4" --include-mc

# まずはAIが認識した曲名・タイムスタンプ（セットリスト）だけ確認したい場合
python main.py "path/to/live.mp4" --dry-run

# 保存されたJSONを手動で微調整した後に分割を実行する場合
python main.py "path/to/live.mp4" --from-json "./output/live/setlist.json"
```

### CLIオプション一覧

| オプション | 型 / デフォルト | 説明 |
| :--- | :--- | :--- |
| `video_path` | 文字列 (必須) | 分割対象のライブ動画ファイルパス |
| `-o`, `--output-dir` | 文字列 (`./output/<動画名>/`) | 分割後動画の保存先フォルダ |
| `--model` | 文字列 (`gemini-3.8-flash`) | 使用するGeminiモデル名 |
| `--margin-start` | 数値 (`2.0`) | 曲開始前の安全マージン秒数（頭切れ防止） |
| `--margin-end` | 数値 (`2.0`) | 曲終了後の安全マージン秒数（余韻切れ防止） |
| `--include-mc` | フラグ (`False`) | MC（トーク）区間も個別に切り出して保存する |
| `--reencode` | フラグ (`False`) | キーフレーム吸着による秒数のズレを防ぐ高精度再エンコードモード |
| `--dry-run` | フラグ (`False`) | 動画分割を行わず、セットリスト解析とJSON保存のみ実行 |
| `--from-json` | 文字列 (`None`) | 既存のセットリストJSONを読み込んで動画分割のみ実行 |

---

## 出力先とファイル構成

デフォルトでは、本プロジェクト内の **`output/<動画ファイル名>/`** フォルダに出力されます。また、実行ログは **`logs/app.log`** に自動保存されます。

```text
output/
└── <動画ファイル名>/
    ├── 01_曲名A.mp4
    ├── 02_曲名B.mp4
    ├── 03_曲名C.mp4
    ├── ...
    └── setlist.json   # AIが認識した曲名・タイムスタンプ・メモの一覧データ

logs/
└── app.log            # 実行履歴およびエラー時の詳細スタックトレース
```

> [!NOTE]
> `output/` および `logs/` フォルダは `.gitignore` によりGit管理外となっているため、切り出された動画や個人ログが誤ってGitにコミットされる心配はありません。

---

## テスト用サンプル動画の生成

手元にライブ動画がない場合でも、以下のコマンドで15秒の動作確認用サンプル動画（`sample_live.mp4`）を生成できます：

```powershell
python create_sample_live.py
```

生成された `sample_live.mp4` を `drag_and_drop_cutter.bat` にドラッグ＆ドロップして動作をテストできます。

---

## 詳細ドキュメント

より詳細な仕様やトラブルシューティングについては、以下のドキュメントをご参照ください：
- 📐 [システム詳細設計書 & アーキテクチャ判断記録 (ADR)](docs/live_movie_auto_cutter/architecture.md)
- ❓ [トラブルシューティング & よくある質問 (FAQ)](docs/live_movie_auto_cutter/troubleshooting.md)
- 📋 [タスク進捗状況 (task.md)](docs/live_movie_auto_cutter/task.md)
- 📝 [実装・検証レポート (walkthrough.md)](docs/live_movie_auto_cutter/walkthrough.md)
