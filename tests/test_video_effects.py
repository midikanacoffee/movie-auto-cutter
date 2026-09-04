import shutil
import subprocess
import unittest
from pathlib import Path

from src.models import VideoEffectsConfig
from src.video_effects import build_filtergraph, escape_ffmpeg_text


class TestVideoEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("./temp_test_fx").resolve()
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.dummy_video = cls.test_dir / "input.mp4"

        # 4秒のテスト動画
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=4:size=320x240:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=4",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            str(cls.dummy_video),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_escape_ffmpeg_text(self):
        text = "Song: 'Love%Life' \\ Live"
        escaped = escape_ffmpeg_text(text)
        self.assertIn("\\:", escaped)
        self.assertIn("\\%", escaped)
        self.assertIn("\\\\", escaped)

    def test_build_filtergraph_all_enabled(self):
        config = VideoEffectsConfig(
            enable_fade=True,
            fade_duration=1.0,
            enable_title_overlay=True,
            overlay_position="bottom_left",
            enable_closing_message=True,
            closing_message="ご視聴ありがとうございました",
        )

        vf, af = build_filtergraph(
            config=config,
            song_title="テスト曲",
            artist_name="DTバンド",
            duration_sec=10.0,
        )

        self.assertIn("fade=t=in", vf)
        self.assertIn("fade=t=out", vf)
        self.assertIn("afade=t=in", af)
        self.assertIn("afade=t=out", af)
        self.assertIn("drawtext", vf)
        self.assertIn("テスト曲", vf)
        self.assertIn("ご視聴ありがとうございました", vf)

    def test_apply_effects_to_video(self):
        config = VideoEffectsConfig(
            enable_fade=True,
            fade_duration=1.0,
            enable_title_overlay=True,
            overlay_position="bottom_right",
        )

        vf, af = build_filtergraph(
            config=config,
            song_title="Opening Song",
            artist_name="Band",
            duration_sec=4.0,
        )

        output_video = self.test_dir / "output_with_effects.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(self.dummy_video),
            "-vf",
            vf,
            "-af",
            af,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            str(output_video),
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        self.assertTrue(output_video.exists())
        self.assertGreater(output_video.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
