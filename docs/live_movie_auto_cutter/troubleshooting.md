# トラブルシューティング & よくある質問 (FAQ)

本ツール利用時によくあるトラブルや疑問、およびその対処法をまとめています。

---

## 1. エラーと対処法

### Q1: `Gemini APIキーが見つかりません` と表示される
* **原因**: プロジェクト直下の `.env` ファイルが存在しないか、APIキーが未設定です。
* **対処法**:
  1. プロジェクト直下の `.env` ファイルを開きます。
  2. `GEMINI_API_KEY=AIzaSy...` のように、ご自身のGemini APIキーを正しく貼り付けて保存してください。
  3. APIキーは [Google AI Studio](https://aistudio.google.com/app/apikey) から無料ですぐに取得できます。

### Q2: `ffmpeg: コマンドが見つかりません` または `FileNotFoundError`
* **原因**: システムに `ffmpeg` がインストールされていないか、環境変数 `PATH` に通っていません。
* **対処法**:
  * Windowsの場合: [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 等からffmpegをダウンロードし、`bin` フォルダへのパスをシステム環境変数 `PATH` に追加してください。
  * ターミナルで `ffmpeg -version` を実行してバージョンが表示されればセットアップ完了です。

---

## 2. 仕上がり（分割クオリティ）の微調整テクニック

### Q3: 演奏の頭（最初の1音）が少し切れてしまう
* **対処法**: 開始前の安全マージン（`--margin-start`）を少し広げてください（デフォルトは2.0秒）。
  ```powershell
  # 開始前マージンを3.5秒にして実行
  python main.py "live.mp4" --margin-start 3.5
  ```

### Q4: プレイヤーによって再生開始時に冒頭が一瞬フリーズする、または秒数が1〜2秒ズレる
* **原因**: 高速無劣化カット（ストリームコピー）では、動画内のキーフレーム（Iフレーム）位置に自動吸着してカットされるためです。
* **対処法**: `--reencode` オプションを付けて実行してください。再エンコードにより、指定した秒数通りに1フレーム単位の高精度でカットされます。
  ```powershell
  python main.py "live.mp4" --reencode
  ```

### Q5: 曲名を修正したい、または秒数を手動で微調整したい
* **対処法**: 一旦 `--dry-run` で解析結果のJSONファイルだけを出力し、テキストエディタで修正してから動画分割を実行できます。
  ```powershell
  # 1. まず解析だけ行い、JSONを生成（動画分割はスキップ）
  python main.py "live.mp4" --dry-run

  # 2. 生成された output/live/setlist.json をメモ帳等で開き、曲名や秒数を微調整

  # 3. 編集したJSONを指定して動画分割を実行
  python main.py "live.mp4" --from-json "./output/live/setlist.json"
  ```

### Q6: MC（メンバーのトーク）も動画として保存したい
* **対処法**: `--include-mc` フラグを指定してください。`01_[MC]_トーク内容.mp4` のように別ファイルとして自動切り出しされます。
  ```powershell
  python main.py "live.mp4" --include-mc
  ```
