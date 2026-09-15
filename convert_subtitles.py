"""Convert UTF-8 SRT subtitles to Traditional Chinese with Taiwanese phrases."""

import argparse
from pathlib import Path
import re
import sys

from opencc import OpenCC


def convert_srt(text: str, converter: OpenCC) -> str:
    """Convert only cue text; preserve numbering, timestamps, tags and newlines."""
    result = []
    in_cue = False
    for line in text.splitlines(keepends=True):
        if not line.strip():
            in_cue = False
        elif "-->" in line:
            in_cue = True
        elif in_cue:
            # Leave HTML tags and common SRT positioning/style overrides intact.
            parts = re.split(r"(<[^>]*>|\{\\[^}]*\})", line)
            line = "".join(
                part if index % 2 else converter.convert(part)
                for index, part in enumerate(parts)
            )
        result.append(line)
    return "".join(result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="將 UTF-8 SRT 簡體字幕轉成台灣繁體中文及常見用語。"
    )
    parser.add_argument("input", type=Path, help="來源 .srt 字幕檔")
    parser.add_argument("-o", "--output", type=Path, help="輸出路徑（預設：原檔名_zh_tw.srt）")
    args = parser.parse_args()
    source = args.input
    output = args.output or source.with_name(f"{source.stem}_zh_tw{source.suffix}")
    try:
        if source.suffix.lower() != ".srt" or output.suffix.lower() != ".srt":
            raise ValueError("來源及輸出檔案都必須是 .srt。")
        if source.resolve() == output.resolve():
            raise ValueError("輸出路徑不可與來源相同，請保留原始字幕。")
        raw = source.read_bytes()
        has_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        if "-->" not in text:
            raise ValueError("找不到 SRT 時間軸，請確認字幕格式。")
        converted = convert_srt(text, OpenCC("s2twp.json"))
        encoded = converted.encode("utf-8-sig" if has_bom else "utf-8")
        # Exclusive creation also prevents accidentally replacing existing output.
        with output.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError:
        print(f"錯誤：輸出檔案已存在：{output}，請用 -o 指定其他檔名。", file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    print(f"已轉換：{source} → {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
