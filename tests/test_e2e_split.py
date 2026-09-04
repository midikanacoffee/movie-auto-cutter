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
                lyrics="La la la",
            ),
            SongSegment(
                index=2,
                title="Member MC",
                start_time="00:00:08",
                end_time="00:00:10",
                segment_type="mc",
            ),
            SongSegment(
                index=3,
                title="Song B",
                start_time="00:00:11",
                end_time="00:00:14",
                segment_type="song",
            ),
        ]
        # 1. separate モード（MCも別ファイルで切り出し、字幕＆YouTube情報も生成）
        output_dir = self.test_dir / "split_separate"
        generated = split_video(
            video_path=self.dummy_video,
            segments=segments,
            output_dir=output_dir,
            margin_start=0.5,
            margin_end=0.5,
            mc_mode="separate",
            generate_subtitles=True,
            generate_youtube_info=True,
        )
        self.assertEqual(len(generated), 3)
        self.assertTrue((output_dir / "01_Song A.mp4").exists())
        self.assertTrue((output_dir / "01_Song A.srt").exists())
        self.assertTrue((output_dir / "01_Song A_youtube_info.txt").exists())
        self.assertTrue((output_dir / "02_[MC]_Member MC.mp4").exists())
        self.assertTrue((output_dir / "03_Song B.mp4").exists())

        # 2. attach モード（前のMCを曲の冒頭に結合）
        output_dir_attach = self.test_dir / "split_attach"
        generated_attach = split_video(
            video_path=self.dummy_video,
            segments=segments,
            output_dir=output_dir_attach,
            margin_start=0.5,
            margin_end=0.5,
            mc_mode="attach",
        )
        self.assertEqual(len(generated_attach), 2)
        self.assertTrue((output_dir_attach / "01_Song A.mp4").exists())
        self.assertTrue((output_dir_attach / "03_[MC+Song]_Song B.mp4").exists())

        # 3. opening / ending を含むフル切り出しテスト
        segments_full = [
            SongSegment(index=1, title="開場・SE", start_time="00:00:00", end_time="00:00:02", segment_type="opening"),
            SongSegment(index=2, title="Song 1", start_time="00:00:03", end_time="00:00:08", segment_type="song"),
            SongSegment(index=3, title="退場・終演", start_time="00:00:09", end_time="00:00:15", segment_type="ending"),
        ]
        output_dir_full = self.test_dir / "split_full"
        generated_full = split_video(
            video_path=self.dummy_video,
            segments=segments_full,
            output_dir=output_dir_full,
            margin_start=0.5,
            margin_end=0.5,
            include_opening=True,
            include_ending=True,
        )
        self.assertEqual(len(generated_full), 3)
        self.assertTrue((output_dir_full / "00_[Opening]_開場・SE.mp4").exists())
        self.assertTrue((output_dir_full / "02_Song 1.mp4").exists())
        self.assertTrue((output_dir_full / "99_[Ending]_退場・終演.mp4").exists())

        # 4. effects_config 適用テスト（フェード＆テロップ合成）
        from src.models import VideoEffectsConfig
        effects = VideoEffectsConfig(
            enable_fade=True,
            fade_duration=0.5,
            enable_title_overlay=True,
            overlay_position="top_left",
        )
        output_dir_fx = self.test_dir / "split_effects"
        generated_fx = split_video(
            video_path=self.dummy_video,
            segments=[segments_full[1]],  # Song 1 (6秒)
            output_dir=output_dir_fx,
            margin_start=0.0,
            margin_end=0.0,
            effects_config=effects,
        )
        self.assertEqual(len(generated_fx), 1)
        fx_file = output_dir_fx / "02_Song 1.mp4"
        self.assertTrue(fx_file.exists())
        self.assertGreater(fx_file.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
