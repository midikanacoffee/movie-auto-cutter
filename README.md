# Live Movie Auto Cutter (ライブ動画 自動曲間認識・分割ツール)

ライブ動画（MP4等）から音声を抽出し、Gemini APIを用いて各楽曲の境界（開始・終了時間）と曲名を自動特定した上で、ffmpegを用いて曲ごとに自動分割・自動命名するローカルツールです。

## 特徴
- **AI曲間認識**: Gemini APIの音声解析により、演奏・MC・インターバルを判別
- **高速・無劣化分割**: ffmpegのストリームコピーによる高速なカット処理
- **安全マージン機能**: 曲頭・曲末が切れないよう前後に自動マージンを設定
- **フォールバック命名**: 曲名が特定できない場合でも歌詞やMC内容から自動命名
- **セキュリティ配慮**: 動画・音声データやAPIキーはGit管理外（`.gitignore`）に隔離

## 必要要件
- Python 3.10以上
- ffmpeg（システム環境変数PATHに通っていること）
- Google Gemini API Key

## セットアップ
1. `.env.example` をコピーして `.env` を作成し、APIキーを設定してください：
   ```bash
   cp .env.example .env
   ```
2. `.env` を開き、`GEMINI_API_KEY` に実際のAPIキーを記述します。
   ※ `.env` ファイルはGitには絶対にコミットされません。

## 使い方

### 方法 1: ドラッグ＆ドロップ（最も簡単）
対象のライブ動画ファイル（`.mp4`, `.mkv`, `.mov` 等）を、プロジェクトフォルダ内にある **`drag_and_drop_cutter.bat`** にドラッグ＆ドロップするだけで自動で処理が開始されます。

### 方法 2: コマンドライン実行
ターミナル（PowerShell等）から詳細オプションを指定して実行できます：

```powershell
# 基本実行（楽曲ごとに自動分割）
python main.py "path/to/live.mp4"

# 出力先フォルダを指定する場合
python main.py "path/to/live.mp4" -o "D:\MySongs"

# MC区間も動画として切り出す場合
python main.py "path/to/live.mp4" --include-mc

# まずはAIが認識した曲名・タイムスタンプ（セットリスト）だけ確認したい場合
python main.py "path/to/live.mp4" --dry-run

# 保存されたJSONを手動で微調整した後に分割を実行する場合
python main.py "path/to/live.mp4" --from-json "./output/live/setlist.json"
```

## 出力先とファイル構成
デフォルトでは、本プロジェクト内の **`output/<動画ファイル名>/`** フォルダに出力されます。

```text
output/
└── <動画ファイル名>/
    ├── 01_曲名A.mp4
    ├── 02_曲名B.mp4
    ├── 03_曲名C.mp4
    ├── ...
    └── setlist.json   # AIが認識した曲名・時間・メモの一覧データ
```

> [!NOTE]
> `output/` フォルダは `.gitignore` によりGit管理外となっているため、切り出された動画ファイルが誤ってGitにコミットされる心配はありません。

