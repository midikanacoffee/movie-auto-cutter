# ライブ動画 自動曲間認識・分割ツール 実装・検証レポート (Walkthrough)

## 概要
ライブ動画ファイルからAI（Gemini API）を用いて楽曲とMCの境界・曲名を自動認識し、ffmpegで曲ごとに自動分割・自動命名するローカルツールの実装と検証を完了しました。

---

## 実装内容

### 1. セキュリティ・プライバシー保護の徹底
- **`.gitignore` の鉄壁化**:
  - APIキー（`.env`, `.env.*`）
  - 動画・音声ファイル全般（`*.mp4`, `*.mov`, `*.mp3`, `*.wav` 等）
  - 一時フォルダ（`temp/`, `output/` 等）
- **クラウドストレージの即時削除**:
  - Gemini Files API にアップロードした音声データは、解析完了後にスクリプト側で即時削除（クリーンアップ）される安全設計。
- **プライベートリポジトリ管理**:
  - GitHub上に非公開（Private）でリポジトリを作成・管理。

### 2. コアモジュール
- `src/models.py`:
  - タイムスタンプ（HH:MM:SS）と秒数の相互変換
  - 安全マージン計算（頭切れ・余韻切れ防止）
  - Windowsファイル名禁止文字のサニタイズ
- `src/audio_extractor.py`:
  - 動画から96kbps MP3への超高速・軽量音声抽出
- `src/gemini_analyzer.py`:
  - Gemini APIによる音声解析（演奏・MC・インターバルの判別、曲名特定、フォールバック命名）
- `src/video_splitter.py`:
  - ffmpegによる無劣化ストリームコピー（数秒で終わる高速カット）
  - 高精度再エンコードモード（オプション）
- `main.py`:
  - CLIエントリーポイント（JSON保存、復元分割 `--from-json`、安全マージン指定等）
- `drag_and_drop_cutter.bat`:
  - 動画ファイルをドラッグ＆ドロップするだけで実行可能なバッチファイル

---

## 検証結果

### 自動テスト (合計 8件 PASSED)
```text
Ran 8 tests in 1.514s - OK
```
1. **データモデル・計算テスト** (`tests/test_models.py`):
   - 秒数変換、フォーマット変換、禁止文字サニタイズ、安全マージン計算（頭切れ防止・動画長クリップ）、JSONシリアライズの正常性を検証。
2. **結合・End-to-Endテスト** (`tests/test_e2e_split.py`):
   - ffmpegによるテスト動画生成
   - 音声抽出（MP3）の実行確認
   - 動画再生時間の取得確認
   - 複数区間へのマージン付き分割・命名確認（`01_Song A.mp4`, `02_Song B.mp4`）

---

## 使い方

### 準備
1. `.env.example` をコピーして `.env` を作成し、Gemini APIキーを設定：
   ```bash
   cp .env.example .env
   # .env を編集して GEMINI_API_KEY=あなたのキー を設定
   ```

### 実行方法

#### 方法A: 最も簡単なドラッグ＆ドロップ
動画ファイル（`.mp4` など）を `drag_and_drop_cutter.bat` にドラッグ＆ドロップするだけです。

#### 方法B: コマンドライン実行
```bash
# 基本実行（楽曲ごとに自動分割）
python main.py "path/to/live_movie.mp4"

# MC区間も動画として切り出す場合
python main.py "path/to/live_movie.mp4" --include-mc

# まずは解析結果（セットリスト）だけ確認したい場合
python main.py "path/to/live_movie.mp4" --dry-run

# 保存されたJSONのタイムスタンプを手動で微調整した後に分割する場合
python main.py "path/to/live_movie.mp4" --from-json "./output/live_movie/setlist.json"
```
