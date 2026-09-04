from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel, Field


def time_str_to_seconds(time_str: str) -> float:
    """HH:MM:SS または MM:SS.sss 形式の文字列を秒数 (float) に変換する。"""
    time_str = time_str.strip()
    parts = time_str.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    return 0.0


def seconds_to_time_str(seconds: float) -> str:
    """秒数を HH:MM:SS 形式の文字列に変換する。"""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def sanitize_filename(name: str) -> str:
    """ファイル名として使用できないWindows/Linux禁止文字を除去・置換する。"""
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized or "untitled"


class YouTubeMetadata(BaseModel):
    """YouTube投稿用メタデータ"""

    title: str = Field(default="", description="YouTube投稿向けタイトル（曲名・アーティスト名・日付等を含む）")
    description: str = Field(default="", description="YouTube概要欄用テキスト（曲紹介、演奏の見どころ等）")
    mood_and_atmosphere: str = Field(default="", description="楽曲や演奏の雰囲気・ノリ（疾走感、エモーショナル、MCの盛り上がり等）")
    recorded_date: str = Field(default="", description="推定されるライブ開催日・収録日（YYYY-MM-DD等）")
    tags: list[str] = Field(default_factory=list, description="YouTube用おすすめハッシュタグ・キーワード一覧")


class VideoEffectsConfig(BaseModel):
    """動画演出・テロップ設定"""

    enable_fade: bool = Field(default=False, description="冒頭フェードインと末尾フェードアウトを適用するか")
    fade_duration: float = Field(default=1.5, description="フェードイン・フェードアウトの秒数")
    enable_title_overlay: bool = Field(default=False, description="曲名・アーティスト名テロップを表示するか")
    overlay_position: Literal["bottom_left", "bottom_right", "top_left", "top_right"] = Field(
        default="bottom_left", description="テロップの表示位置"
    )
    overlay_start_sec: float = Field(default=1.5, description="テロップ表示開始秒数（動画先頭から）")
    overlay_duration: float = Field(default=8.0, description="テロップの表示秒数")
    enable_closing_message: bool = Field(default=False, description="末尾にエンディングメッセージを表示するか")
    closing_message: str = Field(default="ご視聴ありがとうございました", description="エンディングメッセージの内容")

    @property
    def is_active(self) -> bool:
        """何らかの演出が有効になっているか（再エンコードが必要か）"""
        return self.enable_fade or self.enable_title_overlay or self.enable_closing_message


class SongSegment(BaseModel):
    """ライブ動画内の個別区間（楽曲、MC、オープニング、エンディング、インターバル等）の情報"""

    index: int = Field(description="通し番号（1始まり）")
    title: str = Field(description="曲名、または区間タイトル（例: オープニング, メンバー紹介, エンディング）")
    start_time: str = Field(description="開始時間 (HH:MM:SS または MM:SS)")
    end_time: str = Field(description="終了時間 (HH:MM:SS または MM:SS)")
    segment_type: Literal["song", "mc", "opening", "ending", "interval"] = Field(
        default="song",
        description="区間の種類: song(楽曲), mc(トーク), opening(動画開始〜1曲目まで), ending(最終曲終了〜動画末尾), interval(アンコール待ち等)",
    )
    notes: str = Field(
        default="",
        description="判定の根拠（演奏の特徴、MC内容、歓声など）",
    )
    lyrics: str = Field(
        default="",
        description="聞き取れた歌詞のテキスト（聞き取れない場合は空文字）",
    )
    youtube_metadata: YouTubeMetadata | None = Field(
        default=None,
        description="YouTube投稿用メタデータ（説明文、雰囲気、タグなど）",
    )

    @property
    def start_seconds(self) -> float:
        return time_str_to_seconds(self.start_time)

    @property
    def end_seconds(self) -> float:
        return time_str_to_seconds(self.end_time)

    def get_adjusted_range(
        self,
        margin_start: float = 3.5,
        margin_end: float = 3.5,
        max_duration: float | None = None,
    ) -> tuple[float, float]:
        """安全マージン（開始前・終了後）を適用した秒数範囲を返す（デフォルト前後3.5秒）。"""
        adj_start = max(0.0, self.start_seconds - margin_start)
        adj_end = self.end_seconds + margin_end
        if max_duration is not None:
            adj_end = min(max_duration, adj_end)
        return adj_start, adj_end


class LiveAnalysisResult(BaseModel):
    """ライブ全体の解析結果"""

    artist_name: str = Field(default="", description="アーティスト名・バンド名")
    live_title: str = Field(default="", description="ライブタイトルまたは概要")
    recorded_date: str = Field(default="", description="ライブ開催日・収録日時（動画名やMCから推定）")
    segments: list[SongSegment] = Field(
        default_factory=list,
        description="検出された区間（オープニング・曲・MC・エンディング等）の時系列リスト",
    )
