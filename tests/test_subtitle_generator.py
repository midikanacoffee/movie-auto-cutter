import unittest
from pathlib import Path
import shutil

from src.models import SongSegment, YouTubeMetadata
from src.subtitle_generator import create_srt_file, export_youtube_info


class TestSubtitleGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("./temp_test_sub").resolve()
        cls.test_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_create_srt_file(self):
        srt_path = self.test_dir / "test_song.srt"
        lyrics = "最初のフレーズ\nサビの盛り上がり\n最後の余韻"
        result = create_srt_file(srt_path, lyrics, duration_sec=30.0)

        self.assertIsNotNone(result)
        self.assertTrue(srt_path.exists())
        content = srt_path.read_text(encoding="utf-8")
        self.assertIn("最初のフレーズ", content)
        self.assertIn("-->", content)
        self.assertIn("1\n00:00:01,000 -->", content)

    def test_create_srt_empty(self):
        srt_path = self.test_dir / "empty.srt"
        result = create_srt_file(srt_path, "", duration_sec=30.0)
        self.assertIsNone(result)

    def test_export_youtube_info(self):
        info_path = self.test_dir / "01_Song_youtube_info.txt"
        segment = SongSegment(
            index=1,
            title="熱狂のロック",
            start_time="00:01:00",
            end_time="00:04:30",
            segment_type="song",
            lyrics="燃え上がれ ロックンロール",
            youtube_metadata=YouTubeMetadata(
                title="【Live】熱狂のロック - DTバンド (2025.11.03)",
                description="2025年11月3日の熱狂ライブより！最高のギターソロをお見逃しなく！",
                mood_and_atmosphere="エネルギッシュで疾走感あふれる演奏",
                recorded_date="2025-11-03",
                tags=["DTバンド", "ライブ", "ロック", "ギターソロ"],
            ),
        )

        result = export_youtube_info(
            info_path,
            segment=segment,
            artist_name="DTバンド",
            live_title="Live 2025",
            recorded_date="2025-11-03",
        )

        self.assertTrue(result.exists())
        content = result.read_text(encoding="utf-8")
        self.assertIn("【動画タイトル (コピペ用)】", content)
        self.assertIn("【Live】熱狂のロック - DTバンド (2025.11.03)", content)
        self.assertIn("燃え上がれ ロックンロール", content)
        self.assertIn("DTバンド, ライブ, ロック, ギターソロ", content)


if __name__ == "__main__":
    unittest.main()
