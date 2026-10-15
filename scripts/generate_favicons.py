#!/usr/bin/env python3
"""Rasterize brand SVG icons and pack a multi-size favicon.ico.

Generates square PNGs at 48, 96, 192, and 512 from assets/brand/gemmisi-icon.svg.
Leaves the existing 16, 32, and 180 PNGs untouched. Packs favicon.ico with the
kept 16/32 images plus the new 48 image.

Run from the repo root:

    python3 scripts/generate_favicons.py
"""
from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "assets" / "brand" / "gemmisi-icon.svg"
BRAND = ROOT / "assets" / "brand"
FAVICON = ROOT / "favicon.ico"
GENERATE_SIZES = (48, 96, 192, 512)
KEEP_SIZES = (16, 32, 180)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path} is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def rasterize(size: int) -> Path:
    dest = BRAND / f"gemmisi-icon-{size}.png"
    subprocess.check_call(
        [
            "rsvg-convert",
            "-w",
            str(size),
            "-h",
            str(size),
            "-o",
            str(dest),
            str(SVG),
        ]
    )
    image = Image.open(dest).convert("RGBA")
    if image.size != (size, size):
        raise SystemExit(f"{dest} is {image.size}, expected {size}x{size}")
    image.save(dest, format="PNG", optimize=True)
    return dest


def write_ico(dest: Path, png_paths: list[Path]) -> None:
    entries: list[tuple[int, int, bytes]] = []
    for path in png_paths:
        width, height = png_size(path)
        if width > 256 or height > 256:
            raise SystemExit(f"ICO entry too large: {path} {width}x{height}")
        entries.append((width, height, path.read_bytes()))
    offset = 6 + 16 * len(entries)
    buf = bytearray()
    buf += struct.pack("<HHH", 0, 1, len(entries))
    for width, height, blob in entries:
        buf += struct.pack(
            "<BBBBHHII",
            width % 256,
            height % 256,
            0,
            0,
            1,
            32,
            len(blob),
            offset,
        )
        offset += len(blob)
    for _width, _height, blob in entries:
        buf += blob
    dest.write_bytes(bytes(buf))


def ico_sizes(path: Path) -> list[tuple[int, int]]:
    data = path.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data)
    if reserved != 0 or kind != 1 or count < 1:
        raise SystemExit(f"{path} is not a valid ICO")
    sizes = []
    cursor = 6
    for _ in range(count):
        width, height, _colors, _res, _planes, _bits, _nbytes, _off = struct.unpack_from(
            "<BBBBHHII", data, cursor
        )
        sizes.append((width or 256, height or 256))
        cursor += 16
    return sizes


def main() -> None:
    if not SVG.exists():
        raise SystemExit(f"missing {SVG}")
    for size in KEEP_SIZES:
        path = BRAND / f"gemmisi-icon-{size}.png"
        if not path.exists():
            raise SystemExit(f"expected to keep existing {path}")
        width, height = png_size(path)
        if (width, height) != (size, size):
            raise SystemExit(f"{path} is {width}x{height}, expected {size}x{size}")
    written = []
    for size in GENERATE_SIZES:
        written.append(rasterize(size))
    ico_sources = [
        BRAND / "gemmisi-icon-16.png",
        BRAND / "gemmisi-icon-32.png",
        BRAND / "gemmisi-icon-48.png",
    ]
    write_ico(FAVICON, ico_sources)
    sizes = ico_sizes(FAVICON)
    if sizes != [(16, 16), (32, 32), (48, 48)]:
        raise SystemExit(f"favicon.ico sizes {sizes}, expected 16/32/48")
    print("wrote", ", ".join(path.relative_to(ROOT).as_posix() for path in written))
    print("wrote", FAVICON.relative_to(ROOT), "sizes", " ".join(f"{w}x{h}" for w, h in sizes))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print("rsvg-convert is required (librsvg2-bin)", file=sys.stderr)
        raise SystemExit(exc) from exc
