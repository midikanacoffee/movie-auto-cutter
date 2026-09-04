import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.models import LiveAnalysisResult


SYSTEM_PROMPT = """\
あなたはプロの音楽エンジニアおよびライブ音源分析のエキスパートです。
渡されたライブ音声を時系列順に注意深く聴き取り、各楽曲の開始時間・終了時間、曲名、MC区間、および不要なインターバル（長いアンコール待ち・客席歓声など）を正確に分析して構造化データとして返却してください。

【重要な判定基準】
1. **境界（タイムスタンプ）の判定**:
   - 楽曲の開始時間（start_time）: 最初のカウント、ドラム、イントロの第一音が鳴った瞬間。
   - 楽曲の終了時間（end_time）: 演奏が終わり、最後の余韻・拍手が落ち着く瞬間。
   - 曲と曲がシームレスに繋がっている演奏（メドレーなど）の場合: 次の曲のボーカルやメインリフが入る拍の変わり目を境界としてください。
2. **曲名とフォールバック命名**:
   - 既知の楽曲やMCでの曲紹介（「次の曲は〜！」など）、歌詞の聞き取りから曲名を正確に特定してください。
   - 正確な曲名が不明な場合は、「Track_01_歌詞のワンフレーズ」や「Track_02_アップテンポなロック」のように、後から判別しやすいフォールバック名を命名してください。決して空欄にしないでください。
3. **セグメントの種類（segment_type）**:
   - "song": 楽曲演奏
   - "mc": トーク・メンバー紹介・MC
   - "interval": 本編終了後の長いアンコール待ち（手拍子のみが続く時間など）や会場のBGM区間
4. **時間の表記**:
   - "HH:MM:SS" または "MM:SS" のフォーマットで記述してください（例: "00:04:15" または "04:15"）。
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
    uploaded_file = client.files.upload(file=str(audio_path))

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
