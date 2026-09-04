# システム設計書 & アーキテクチャ判断記録 (Architecture & ADR)

本ドキュメントでは、Live Movie Auto Cutter の内部アーキテクチャ、処理パイプライン、および主要な設計判断理由（ADR: Architectural Decision Records）をまとめます。

---

## 1. システムアーキテクチャ概要

```mermaid
flowchart TD
    Video[元動画ファイル .mp4 / .mkv 等] --> Extractor[src/audio_extractor.py]
    Extractor -->|軽量MP3 96kbps 抽出| TempAudio[temp/video_extracted.mp3]
    
    TempAudio --> GeminiClient[src/gemini_analyzer.py]
    GeminiClient -->|Files APIアップロード| GeminiAPI[Google Gemini 3.8 Flash]
    
    GeminiAPI -->|JSON構造化データ| Result[LiveAnalysisResult]
    GeminiClient -->|解析完了後 即時削除| DeleteCloud[クラウド上ファイル削除]
    
    Result --> JSONSave[output/動画名/setlist.json]
    Result --> Splitter[src/video_splitter.py]
    
    Video --> Splitter
    Splitter -->|安全マージン適用 & ffmpeg無劣化カット| OutputDir[output/動画名/]
    OutputDir --> Files["01_曲名A.mp4<br/>02_曲名B.mp4<br/>03_曲名C.mp4"]
```

---

## 2. 主要な設計判断理由 (ADRs)

### ADR-01: 動画ではなく「96kbps MP3」を抽出してAPIに送信する
* **背景**: ライブ動画（フルHD/4K）は数GB〜数十GBあり、直接APIへアップロードすると通信時間が膨大になり、API容量制限（通常2GB等）に抵触する。
* **決定**: ローカルのffmpegで96kbpsのMP3を一時生成し、音声のみをGeminiに送信する。
* **効果**:
  * データサイズを約99%削減（2時間のライブでも約80MB程度）。
  * アップロードが数秒〜十数秒で完了し、大幅な高速化とAPIコスト削減を達成。
  * 歌詞の聞き取り・曲間認識には96kbpsで十分な精度が保たれる。

### ADR-02: デフォルトで「無劣化ストリームコピー (`-c copy`)」を採用
* **背景**: 動画の再エンコードはCPU/GPUに負荷がかかり、2時間の動画の分割に数十分以上を要する上、画質が劣化する。
* **決定**: デフォルトではffmpegの `-c copy`（無劣化切り出し）を採用し、指定秒数通りの完全フレーム精度が必要な場合のみ `--reencode` オプションを提供する。
* **効果**:
  * 1曲あたりわずか数秒、全体でも数十秒で分割が完了。
  * 元動画の画質・音質を100%維持。

### ADR-03: 安全マージン（デフォルト前後2.0秒）の自動付与
* **背景**: LLM（AI）の認識するタイムスタンプには1〜2秒程度の誤差が生じる可能性があり、演奏の最初の音（アタック音）や最後の余韻が切れてしまうリスクがある。
* **決定**: 認識された開始時刻の「2秒前」、終了時刻の「2秒後」を自動的に切り出し範囲として計算する（0秒未満や総尺超過は自動クリップ）。
* **効果**: 演奏の頭切れ・余韻切れを確実に防止。

### ADR-04: クラウドストレージの即時削除（プライバシー保護）
* **背景**: ユーザーのライブ動画・音声データがクラウド上に残り続けることはプライバシー・著作権上望ましくない。
* **決定**: `src/gemini_analyzer.py` の `finally` 節で、Gemini Files API に登録された音声ファイルを解析終了直後に自動削除する。
* **効果**: クラウド側に個人データや音声が残留しないクリーンな運用を保証。
