"""Generate small cover images from song/*.zip JACKET entries."""

import argparse
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_IMAGE_BYTES = 32 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 40_000_000


def chart_text(data):
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return None


def make_cover(archive, destination):
    with zipfile.ZipFile(archive) as package:
        entries = {item.filename.replace("\\", "/"): item for item in package.infolist()}
        for name, chart_entry in entries.items():
            if not name.lower().endswith(".2d") or chart_entry.file_size > 2_000_000:
                continue
            text = chart_text(package.read(chart_entry))
            if not text:
                continue
            match = re.search(r"^\s*JACKET\s*:\s*(.+?)\s*$", text, re.IGNORECASE | re.MULTILINE)
            if not match:
                continue
            jacket_path = PurePosixPath(match.group(1).strip().strip('"').replace("\\", "/"))
            if jacket_path.is_absolute() or ".." in jacket_path.parts:
                continue
            image_name = str(PurePosixPath(name).parent / jacket_path)
            image_entry = entries.get(image_name)
            if not image_entry or image_entry.file_size > MAX_IMAGE_BYTES:
                continue
            try:
                with Image.open(io.BytesIO(package.read(image_entry))) as source:
                    source = ImageOps.exif_transpose(source)
                    cover = ImageOps.fit(source.convert("RGB"), (256, 256), method=Image.Resampling.LANCZOS)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    cover.save(destination, "WEBP", quality=82, method=6)
                return True
            except (UnidentifiedImageError, OSError, ValueError):
                continue
    return False


def read_difficulties(archive):
    result = []
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            if not entry.filename.lower().endswith(".2d") or entry.file_size > 2_000_000:
                continue
            source = chart_text(package.read(entry))
            if not source:
                continue
            difficulty = None
            for line in source.splitlines():
                match = re.match(r"^\s*(DIFFICULTY|LEVEL)\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
                if not match:
                    continue
                if match.group(1).upper() == "DIFFICULTY":
                    difficulty = match.group(2).strip()
                elif difficulty and re.fullmatch(r"\d{1,3}", match.group(2)):
                    item = {"name": difficulty, "level": int(match.group(2))}
                    if item not in result:
                        result.append(item)
                    difficulty = None
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--song-dir", type=Path, default=Path("song"))
    parser.add_argument("--output-dir", type=Path, default=Path("song/covers"))
    args = parser.parse_args()
    metadata = {}
    for archive in sorted(args.song_dir.glob("*.zip")):
        destination = args.output_dir / f"{archive.stem}.webp"
        try:
            metadata[archive.name] = {"difficulties": read_difficulties(archive)}
            if make_cover(archive, destination):
                print(f"Created {destination}")
            else:
                print(f"No usable JACKET: {archive}")
        except (OSError, zipfile.BadZipFile) as error:
            print(f"Skipped {archive}: {error}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "index.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
