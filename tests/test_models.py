import unittest
from src.models import (
    LiveAnalysisResult,
    SongSegment,
    sanitize_filename,
    seconds_to_time_str,
    time_str_to_seconds,
)


class TestModels(unittest.TestCase):
    def test_time_str_to_seconds(self):
        self.assertEqual(time_str_to_seconds("00:01:30"), 90.0)
        self.assertEqual(time_str_to_seconds("01:30"), 90.0)
        self.assertEqual(time_str_to_seconds("01:00:00"), 3600.0)
        self.assertEqual(time_str_to_seconds("00:00:15.500"), 15.5)
        self.assertEqual(time_str_to_seconds("invalid"), 0.0)

    def test_seconds_to_time_str(self):
        self.assertEqual(seconds_to_time_str(90.0), "00:01:30.000")
        self.assertEqual(seconds_to_time_str(3665.5), "01:01:05.500")
        self.assertEqual(seconds_to_time_str(-10), "00:00:00.000")

    def test_sanitize_filename(self):
        self.assertEqual(
            sanitize_filename('Song: "Title" / AC/DC? <Live>'),
            "Song_ _Title_ _ AC_DC_ _Live_",
        )
        self.assertEqual(sanitize_filename("Normal Song Name"), "Normal Song Name")
        self.assertEqual(sanitize_filename("   "), "untitled")

    def test_adjusted_range_margins(self):
        seg = SongSegment(
            index=1,
            title="Test Song",
            start_time="00:01:00",
            end_time="00:04:00",
            segment_type="song",
        )
        # デフォルトマージン（前2秒、後2秒）
        adj_start, adj_end = seg.get_adjusted_range(margin_start=2.0, margin_end=2.0)
        self.assertEqual(adj_start, 58.0)  # 60 - 2
        self.assertEqual(adj_end, 242.0)   # 240 + 2

        # 動画長上限クリップ
        adj_start, adj_end = seg.get_adjusted_range(
            margin_start=2.0, margin_end=2.0, max_duration=241.0
        )
        self.assertEqual(adj_end, 241.0)

        # 0秒未満にならないこと
        seg_start_zero = SongSegment(
            index=1,
            title="Opening",
            start_time="00:00:01",
            end_time="00:01:00",
        )
        adj_start, adj_end = seg_start_zero.get_adjusted_range(margin_start=3.0, margin_end=1.0)
        self.assertEqual(adj_start, 0.0)

    def test_live_analysis_result_json(self):
        json_data = """
        {
            "artist_name": "Test Band",
            "live_title": "Live 2026",
            "segments": [
                {
                    "index": 1,
                    "title": "Opening Song",
                    "start_time": "00:00:10",
                    "end_time": "00:03:30",
                    "segment_type": "song",
                    "notes": "Intro count heard"
                },
                {
                    "index": 2,
                    "title": "Member MC",
                    "start_time": "00:03:31",
                    "end_time": "00:05:00",
                    "segment_type": "mc",
                    "notes": "Greeting"
                }
            ]
        }
        """
        result = LiveAnalysisResult.model_validate_json(json_data)
        self.assertEqual(result.artist_name, "Test Band")
        self.assertEqual(len(result.segments), 2)
        self.assertEqual(result.segments[0].title, "Opening Song")
        self.assertEqual(result.segments[1].segment_type, "mc")


if __name__ == "__main__":
    unittest.main()
