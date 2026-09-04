import json
import shutil
import subprocess
import unittest
from pathlib import Path

from src.audio_extractor import extract_audio, get_video_duration
from src.models import LiveAnalysisResult, SongSegment
from src.video_splitter import split_video


class TestEndToEndSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("./temp_test").resolve()
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.dummy_video = cls.test_dir / "test_live.mp4"

        # ffmpegで15秒のテスト動画（カラーバー＋サイン波音声）を生成
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=15:size=320x240:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=15",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(cls.dummy_video),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_audio_extraction(self):
        output_audio = self.test_dir / "extracted.mp3"
        result_path = extract_audio(self.dummy_video, output_audio)
        self.assertTrue(result_path.exists())
        self.assertGreater(result_path.stat().st_size, 0)

    def test_video_duration(self):
        duration = get_video_duration(self.dummy_video)
        self.assertAlmostEqual(duration, 15.0, delta=1.0)

    def test_video_split(self):
        segments = [
            SongSegment(
                index=1,
                title="Song A",
                start_time="00:00:02",
                end_time="00:00:07",
                segment_type="song",
            ),
            SongSegment(
                index=2,
                title="Song B",
                start_time="00:00:08",
                end_time="00:00:13",
                segment_type="song",
            ),
        ]
        output_dir = self.test_dir / "split_output"
        generated = split_video(
            video_path=self.dummy_video,
            segments=segments,
            output_dir=output_dir,
            margin_start=1.0,
            margin_end=1.0,
        )
        self.assertEqual(len(generated), 2)
        self.assertTrue((output_dir / "01_Song A.mp4").exists())
        self.assertTrue((output_dir / "02_Song B.mp4").exists())


if __name__ == "__main__":
    unittest.main()
