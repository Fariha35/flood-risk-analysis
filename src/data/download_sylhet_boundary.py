#!/usr/bin/env python3
"""
Download the Sylhet Division administrative boundary as GeoJSON.

The script queries the Bangladesh government ArcGIS Feature Service used by
this project, selects the ADM1 feature named "Sylhet", validates the response,
and saves it to:

    data/raw/boundaries/sylhet_division.geojson

Only Python's standard library is required.

Usage
-----
From the repository root:

    python src/data/download_sylhet_boundary.py

To overwrite an existing file:

    python src/data/download_sylhet_boundary.py --overwrite
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SERVICE_URL = (
    "https://gis.dghs.gov.bd/server/rest/services/Hosted/"
    "bgd_admbnda_adm1_bbs_20201113/FeatureServer/0/query"
)
DEFAULT_OUTPUT = Path("data/raw/boundaries/sylhet_division.geojson")
TARGET_NAME = "Sylhet"


def build_query_url() -> str:
    """Build the ArcGIS REST query URL for the Sylhet ADM1 polygon."""
    params = {
        "where": f"adm1_en='{TARGET_NAME}'",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    return f"{SERVICE_URL}?{urlencode(params)}"


def download_json(url: str, timeout: int = 60) -> dict[str, Any]:
    """Download and decode a JSON/GeoJSON response."""
    request = Request(
        url,
        headers={
            "User-Agent": (
                "flood-risk-analysis/1.0 "
                "(research data acquisition; GitHub project)"
            ),
            "Accept": "application/geo+json, application/json",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        raise RuntimeError(
            f"Boundary service returned HTTP {exc.code}: {exc.reason}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not connect to the boundary service: {exc.reason}"
        ) from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Boundary service returned invalid JSON/GeoJSON.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected response type from boundary service.")

    return payload


def validate_geojson(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate that the response contains exactly one Sylhet polygon feature."""
    if payload.get("type") != "FeatureCollection":
        error = payload.get("error")
        if error:
            raise RuntimeError(f"ArcGIS service error: {error}")
        raise RuntimeError("Expected a GeoJSON FeatureCollection.")

    features = payload.get("features")
    if not isinstance(features, list):
        raise RuntimeError("GeoJSON response is missing a valid 'features' list.")

    if len(features) != 1:
        raise RuntimeError(
            f"Expected exactly one Sylhet ADM1 feature, received {len(features)}."
        )

    feature = features[0]
    if not isinstance(feature, dict):
        raise RuntimeError("The returned GeoJSON feature is invalid.")

    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise RuntimeError("The returned feature has no valid properties.")

    name = properties.get("adm1_en")
    if name != TARGET_NAME:
        raise RuntimeError(
            f"Expected adm1_en='{TARGET_NAME}', received {name!r}."
        )

    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        raise RuntimeError("The Sylhet feature has no valid geometry.")

    geometry_type = geometry.get("type")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise RuntimeError(
            f"Expected Polygon/MultiPolygon geometry, received {geometry_type!r}."
        )

    coordinates = geometry.get("coordinates")
    if not coordinates:
        raise RuntimeError("The Sylhet feature geometry contains no coordinates.")

    return feature


def write_geojson(
    payload: dict[str, Any],
    output_path: Path,
    *,
    source_url: str,
    overwrite: bool,
) -> None:
    """Write validated GeoJSON atomically and include acquisition metadata."""
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"{output_path} already exists. Use --overwrite to replace it."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    enriched = dict(payload)
    enriched["metadata"] = {
        "study_area": "Sylhet Division, Bangladesh",
        "administrative_level": "ADM1",
        "source_service": SERVICE_URL.rsplit("/query", 1)[0],
        "query_url": source_url,
        "requested_output_crs": "EPSG:4326",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary_path.write_text(
            json.dumps(enriched, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the Sylhet Division ADM1 boundary as GeoJSON."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file if it already exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    query_url = build_query_url()

    print("Downloading Sylhet Division boundary...")
    try:
        payload = download_json(query_url)
        feature = validate_geojson(payload)
        write_geojson(
            payload,
            args.output,
            source_url=query_url,
            overwrite=args.overwrite,
        )
    except (RuntimeError, FileExistsError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    properties = feature["properties"]
    print(f"Saved: {args.output}")
    print(f"ADM1: {properties.get('adm1_en')}")
    print(f"ADM1 code: {properties.get('adm1_pcode', 'N/A')}")
    print("Requested CRS: EPSG:4326")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
