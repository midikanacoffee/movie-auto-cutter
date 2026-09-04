import shutil
import subprocess
import unittest
from pathlib import Path

from src.audio_extractor import extract_audio
from src.logger import setup_logger


class TestJapaneseFilenameAndLogging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("./temp_test_jp").resolve()
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        # 日本語ファイル名
        cls.jp_video = cls.test_dir / "DTバンド LIVE 20251103.mp4"

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=2:size=320x240:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(cls.jp_video),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_audio_extraction_with_japanese_path(self):
        output_audio = self.test_dir / "extracted_ascii.mp3"
        result_path = extract_audio(self.jp_video, output_audio)
        self.assertTrue(result_path.exists())
        self.assertGreater(result_path.stat().st_size, 0)

    def test_logger_file_output(self):
        log_dir = self.test_dir / "logs"
        logger = setup_logger(log_dir)
        logger.info("日本語テストログメッセージ")
        logger.error("テストエラーメッセージ")

        log_file = log_dir / "app.log"
        self.assertTrue(log_file.exists())
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("日本語テストログメッセージ", content)
        self.assertIn("テストエラーメッセージ", content)


if __name__ == "__main__":
    unittest.main()
