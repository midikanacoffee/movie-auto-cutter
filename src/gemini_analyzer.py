import os
import shutil
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.models import LiveAnalysisResult


SYSTEM_PROMPT = """\
あなたはプロの音楽エンジニアおよびライブ音源分析のエキスパートです。
渡されたライブ音声を時系列順に注意深く聴き取り、オープニング、楽曲演奏、MC、エンディング、およびインターバル区間を正確に分析して構造化データとして返却してください。

【重要な区間の種類（segment_type）と判定基準】
1. **"opening" (オープニング区間)**:
   - 動画の最初（00:00）から、1曲目の演奏が始まる直前まで（開演前のSE、入場シーン、歓声、冒頭の挨拶など）。
2. **"song" (楽曲演奏区間)**:
   - 楽曲の演奏区間。
   - start_time: 最初のカウント、ドラム、イントロの第一音が鳴った瞬間。
   - end_time: 演奏が終わり、最後の余韻・拍手が落ち着く瞬間。
   - メドレーなど曲が繋がっている場合は拍の変わり目で区切ってください。
3. **"mc" (MC・トーク区間)**:
   - 曲と曲の間のメンバーによるトーク、MC、曲紹介、メンバー紹介。
4. **"ending" (エンディング区間)**:
   - 最後の曲の演奏終了後から、動画の最後まで（最後の退場挨拶、カーテンコール、客席の拍手、終演アナウンスなど）。
5. **"interval" (インターバル区間)**:
   - 本編終了後の長いアンコール待ち（手拍子のみが続く長大な時間）など。

【曲名とメタデータ】
- **曲名**: 既知曲やMC紹介、歌詞から正確に特定。不明な場合は「Track_01_特徴」などのフォールバック名を命名（決して空欄にしない）。
- **歌詞（lyrics）**: はっきりと聞き取れるサビやタイトルフレーズのみ記載。爆音等で聞き取れない場合は無理に推測せず空文字（""）にしてください。
- **YouTube用メタデータ（youtube_metadata）**:
  - title: 【Live】曲名 - アーティスト名 (日付等)
  - description: 視聴者を引き込む魅力的な概要欄説明文（曲紹介・見どころなど）
  - mood_and_atmosphere: 演奏や会場の雰囲気（例: 「疾走感あふれるロックナンバー」「熱いコール＆レスポンス」など）
  - recorded_date: MCでの発言やファイル名から推測されるライブ開催日時
  - tags: おすすめタグ一覧（5〜10個）

【時間の表記】
- "HH:MM:SS" または "MM:SS" のフォーマット（例: "00:04:15" または "04:15"）。
"""


def get_gemini_client() -> genai.Client:
    """環境変数または.envファイルからAPIキーを読み込み、Geminiクライアントを初期化する。"""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini APIキーが見つかりません。\n"
            "プロジェクト直下に `.env` ファイルを作成し、`GEMINI_API_KEY=あなたのキー` を設定してください。\n"
            "（.env.example をコピーして編集できます）"
        )
    return genai.Client(api_key=api_key)


def analyze_live_audio(
    audio_path: Path,
    model_name: str = "gemini-3.8-flash",
) -> LiveAnalysisResult:
    """音声ファイルをGemini APIにアップロードして解析し、各曲のタイムスタンプと曲名を取得する。

    セキュリティ・プライバシー保護のため、解析完了後はGemini Files APIから
    アップロードした音声ファイルを自動的に削除（クリーンアップ）します。

    Args:
        audio_path: 解析対象の音声ファイルパス (.mp3等)
        model_name: 使用するGeminiモデル名

    Returns:
        LiveAnalysisResult: 検出された各曲・MCのリスト
    """
    client = get_gemini_client()

    print(f"[1/3] 音声ファイルをGemini APIにアップロード中: {audio_path.name}")

    # 日本語等の非ASCII文字が含まれている場合、HTTPヘッダーのUnicodeEncodeErrorを防ぐためASCII名の一時ファイルを使用
    safe_upload_path = audio_path
    temp_ascii_copy = None
    try:
        audio_path.name.encode("ascii")
    except UnicodeEncodeError:
        ascii_filename = f"upload_{uuid.uuid4().hex[:8]}{audio_path.suffix}"
        temp_ascii_copy = audio_path.parent / ascii_filename
        shutil.copy2(audio_path, temp_ascii_copy)
        safe_upload_path = temp_ascii_copy

    try:
        uploaded_file = client.files.upload(file=str(safe_upload_path))
    finally:
        if temp_ascii_copy and temp_ascii_copy.exists():
            try:
                temp_ascii_copy.unlink()
            except Exception:
                pass

    try:
        # アップロードしたファイルの処理完了（ACTIVE状態）を待機
        while uploaded_file.state == "PROCESSING":
            print("  - 音声の処理を待機中...")
            time.sleep(3)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state != "ACTIVE":
            raise RuntimeError(
                f"音声ファイルのアップロード状態が異常です: {uploaded_file.state}"
            )

        print("[2/3] Geminiによるライブ音声の曲間・セットリスト解析中...")

        prompt = (
            "このライブ音声全体を分析し、楽曲の演奏区間、MC区間、インターバル区間を時系列順に特定してください。"
            "曲の開始・終了時刻と曲名を正確に出力してください。"
        )

        models_to_try = [model_name]
        for candidate in ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest"]:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error = None
        for current_model in models_to_try:
            for attempt in range(1, 3):
                try:
                    if current_model != model_name:
                        print(f"  - 代替モデル ({current_model}) に自動切り替えして解析中...")
                    else:
                        print(f"  - モデル ({current_model}) で解析中 (試行 {attempt}/2)...")

                    response = client.models.generate_content(
                        model=current_model,
                        contents=[uploaded_file, prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=LiveAnalysisResult,
                            temperature=0.2,
                        ),
                    )

                    print("[3/3] 解析完了！結果をパース中...")
                    result = LiveAnalysisResult.model_validate_json(response.text)
                    return result

                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                        print(f"  ! {current_model} が一時的に高負荷です。3秒待機して再試行します...")
                        time.sleep(3)
                        continue
                    else:
                        break

        if last_error:
            raise last_error

    finally:
        # プライバシー保護・クラウドストレージ容量クリーンアップのため、アップロードファイルを即時削除
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass
