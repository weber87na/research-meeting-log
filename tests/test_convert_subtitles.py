import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from opencc import OpenCC

from convert_subtitles import convert_srt


class SubtitleTests(unittest.TestCase):
    def test_taiwanese_phrases_and_structure(self):
        source = '1\r\n00:00:01,000 --> 00:00:03,000\r\n<i title="软件">软件和鼠标</i>\r\n\r\n'
        expected = '1\r\n00:00:01,000 --> 00:00:03,000\r\n<i title="软件">軟體和滑鼠</i>\r\n\r\n'
        self.assertEqual(convert_srt(source, OpenCC("s2twp.json")), expected)

    def test_cli_preserves_source_bom_and_existing_output(self):
        script = Path(__file__).resolve().parents[1] / "convert_subtitles.py"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "字幕.srt"
            raw = '1\r\n00:00:01,000 --> 00:00:02,000\r\n软件\r\n'.encode("utf-8-sig")
            source.write_bytes(raw)
            command = [sys.executable, str(script), str(source)]
            first = subprocess.run(command, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            output = source.with_name("字幕_zh_tw.srt")
            expected = raw.replace("软件".encode(), "軟體".encode())
            self.assertEqual(output.read_bytes(), expected)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            self.assertEqual(output.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
