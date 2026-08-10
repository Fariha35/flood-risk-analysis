#!/usr/bin/env python3
"""
Download and clip Bangladesh Inundation History rasters to Sylhet Division.

This script reads the public CyVerse WebDAV directory, discovers the available
GeoTIFF files, downloads them one at a time, clips each raster to the Sylhet
ADM1 boundary, and writes the clipped rasters to data/interim/flood/.

The raw national-scale TIFF is deleted after clipping by default so that a
Colab session does not need to hold the full multi-gigabyte archive.

Dataset
-------
Bangladesh Inundation History
DOI: 10.25739/2edm-jh03
Publisher: CyVerse Data Commons

Examples
--------
Process the first 3 files as a safe test:

    python src/data/process_flood_history.py --max-files 3

Process a date range:

    python src/data/process_flood_history.py \
        --start-date 2001-09-10 \
        --end-date 2001-12-31

Process every discovered raster:

    python src/data/process_flood_history.py

Resume behavior
---------------
If an output TIFF already exists, it is skipped unless --overwrite is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urljoin

import requests
import rasterio
from rasterio.mask import mask


DATASET_DIR_URL = (
    "https://data.cyverse.org/dav-anon/iplant/commons/cyverse_curated/"
    "Giezendanner_BangladeshInundationHistory_Mai2023/"
    "CVPR23FractionalInundationHistory/"
)

DEFAULT_BOUNDARY = Path("data/raw/boundaries/sylhet_division.geojson")
DEFAULT_RAW_DIR = Path("data/raw/flood")
DEFAULT_OUTPUT_DIR = Path("data/interim/flood")

TIFF_NAME_RE = re.compile(r"(?P<timestamp>\d{13})\.tiff$", re.IGNORECASE)


class LinkParser(HTMLParser):
    """Collect href values from a simple WebDAV/browser directory listing."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


def timestamp_name_to_date(filename: str) -> datetime:
    """Convert the 13-digit millisecond Unix timestamp filename to UTC."""
    match = TIFF_NAME_RE.search(filename)
    if not match:
        raise ValueError(f"Unexpected TIFF filename: {filename}")
    timestamp_ms = int(match.group("timestamp"))
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def discover_tiffs(session: requests.Session, timeout: int) -> list[tuple[str, str, datetime]]:
    """Discover TIFF files from the public CyVerse WebDAV directory listing."""
    response = session.get(DATASET_DIR_URL, timeout=timeout)
    response.raise_for_status()

    parser = LinkParser()
    parser.feed(response.text)

    discovered: dict[str, tuple[str, str, datetime]] = {}

    for href in parser.hrefs:
        decoded = unquote(href)
        name = Path(decoded.rstrip("/")).name
        if not TIFF_NAME_RE.fullmatch(name):
            continue

        try:
            date = timestamp_name_to_date(name)
        except ValueError:
            continue

        discovered[name] = (name, urljoin(DATASET_DIR_URL, href), date)

    files = sorted(discovered.values(), key=lambda item: item[2])

    if not files:
        raise RuntimeError(
            "No TIFF files were discovered from the CyVerse directory listing. "
            "The public directory layout may have changed."
        )

    return files


def load_shapes(boundary_path: Path) -> list[dict]:
    """Read GeoJSON geometries for raster masking."""
    if not boundary_path.exists():
        raise FileNotFoundError(
            f"Boundary file not found: {boundary_path}. "
            "Run download_sylhet_boundary.py first."
        )

    with boundary_path.open("r", encoding="utf-8") as handle:
        boundary = json.load(handle)

    features = boundary.get("features")
    if not isinstance(features, list) or not features:
        raise RuntimeError("Boundary GeoJSON contains no features.")

    shapes = [
        feature["geometry"]
        for feature in features
        if isinstance(feature, dict) and feature.get("geometry")
    ]

    if not shapes:
        raise RuntimeError("Boundary GeoJSON contains no valid geometries.")

    return shapes


def download_file(
    session: requests.Session,
    url: str,
    destination: Path,
    timeout: int,
) -> None:
    """Stream a remote TIFF to disk without loading the whole file into RAM."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")

    try:
        with session.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def clip_raster(input_path: Path, output_path: Path, shapes: Iterable[dict]) -> tuple[int, int]:
    """Clip a raster to the supplied GeoJSON shapes and save it."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(input_path) as src:
        clipped, transform = mask(src, list(shapes), crop=True)

        metadata = src.meta.copy()
        metadata.update(
            {
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform,
            }
        )

        temporary = output_path.with_suffix(output_path.suffix + ".part")
        try:
            with rasterio.open(temporary, "w", **metadata) as dst:
                dst.write(clipped)
            temporary.replace(output_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    return clipped.shape[1], clipped.shape[2]


def parse_date(value: str) -> datetime:
    """Parse YYYY-MM-DD as a UTC datetime."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}; expected YYYY-MM-DD."
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and clip Bangladesh inundation rasters to Sylhet."
    )
    parser.add_argument(
        "--boundary",
        type=Path,
        default=DEFAULT_BOUNDARY,
        help=f"Sylhet boundary GeoJSON (default: {DEFAULT_BOUNDARY})",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help=f"Temporary raw TIFF directory (default: {DEFAULT_RAW_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Clipped raster directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--start-date",
        type=parse_date,
        help="First date to process, inclusive (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=parse_date,
        help="Last date to process, inclusive (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="Maximum number of files to process after date filtering.",
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Keep national-scale TIFFs after successful clipping.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download/re-create outputs that already exist.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds (default: 120).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.max_files is not None and args.max_files <= 0:
        print("ERROR: --max-files must be greater than zero.", file=sys.stderr)
        return 2

    if args.start_date and args.end_date and args.start_date > args.end_date:
        print("ERROR: --start-date is after --end-date.", file=sys.stderr)
        return 2

    try:
        shapes = load_shapes(args.boundary)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "flood-risk-analysis/1.0 "
                "(research data acquisition; GitHub project)"
            )
        }
    )

    print("Discovering Bangladesh Inundation History TIFFs...")
    try:
        files = discover_tiffs(session, args.timeout)
    except (requests.RequestException, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.start_date:
        files = [item for item in files if item[2] >= args.start_date]
    if args.end_date:
        end_of_day = args.end_date.replace(hour=23, minute=59, second=59)
        files = [item for item in files if item[2] <= end_of_day]
    if args.max_files is not None:
        files = files[: args.max_files]

    if not files:
        print("No rasters match the requested filters.")
        return 0

    print(f"Selected {len(files)} raster(s).")

    completed = 0
    skipped = 0
    failed = 0

    for index, (remote_name, url, date) in enumerate(files, start=1):
        date_label = date.strftime("%Y_%m_%d")
        raw_path = args.raw_dir / remote_name
        output_path = args.output_dir / f"sylhet_{date_label}.tiff"

        print(
            f"[{index}/{len(files)}] {date.date().isoformat()} -> "
            f"{output_path}"
        )

        if output_path.exists() and not args.overwrite:
            print("  skip: output already exists")
            skipped += 1
            continue

        try:
            if not raw_path.exists() or args.overwrite:
                print("  downloading...")
                download_file(session, url, raw_path, args.timeout)

            print("  clipping to Sylhet...")
            height, width = clip_raster(raw_path, output_path, shapes)
            print(f"  saved: {output_path} ({height} x {width})")
            completed += 1

            if not args.keep_raw and raw_path.exists():
                raw_path.unlink()
                print("  removed temporary national-scale TIFF")

        except (requests.RequestException, OSError, RuntimeError) as exc:
            failed += 1
            print(f"  ERROR: {exc}", file=sys.stderr)
            if raw_path.exists() and not args.keep_raw:
                try:
                    raw_path.unlink()
                except OSError:
                    pass

    print()
    print("Finished.")
    print(f"Completed: {completed}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
