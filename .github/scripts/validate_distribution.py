"""Validate a Dalamud distribution without loading or executing the plugin."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import BadZipFile, ZipFile


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def version_key(value: str) -> tuple[int, ...]:
    require(isinstance(value, str) and re.fullmatch(r"\d+\.\d+\.\d+\.\d+", value) is not None,
            "AssemblyVersion must contain four numeric components")
    parts = tuple(map(int, value.split(".")))
    require(all(0 <= item <= 65534 for item in parts), "Version component is out of range")
    return parts


def release_info(root: Path, repository: str, branch: str, legacy: bool = False) -> tuple[dict, Path]:
    data = json.loads((root / "repo.json").read_text(encoding="utf-8-sig"))
    require(isinstance(data, list) and len(data) == 1, "repo.json must be an array containing one plugin")
    entry = data[0]
    identity = entry.get("InternalName")
    require(identity == "PlayerTrackEnhanced" or (legacy and identity == "PlayerTrack"), "Unexpected plugin identity")
    version = entry.get("AssemblyVersion")
    version_key(version)
    relative = f"plugins/{identity}/{version}/latest.zip"
    expected = f"https://raw.githubusercontent.com/{repository}/{branch}/{relative}"
    for key in ("DownloadLinkInstall", "DownloadLinkUpdate", "DownloadLinkTesting"):
        require(entry.get(key) == expected, f"{key} must use the versioned download in this repository")
    require(entry.get("RepoUrl") == f"https://github.com/{repository}", "Repository URL mismatch")
    require(isinstance(entry.get("DalamudApiLevel"), int) and entry["DalamudApiLevel"] > 0, "Missing Dalamud API level")
    return entry, root / relative


def payload_digest(path: Path) -> str:
    """Ignore archive timestamps/compression when comparing an existing published version."""
    digest = hashlib.sha256()
    with ZipFile(path) as archive:
        for item in sorted(archive.infolist(), key=lambda item: item.filename):
            digest.update(item.filename.encode("utf-8") + b"\0")
            digest.update(hashlib.sha256(archive.read(item)).digest())
    return digest.hexdigest()


def validate(root: Path, repository: str, branch: str = "main", previous_root: Path | None = None) -> dict:
    root = root.resolve()
    entry, path = release_info(root, repository, branch)
    require(path.is_file() and path.stat().st_size < 25 * 1024 * 1024, "Missing ZIP or ZIP exceeds the 25 MiB upload limit")
    expected_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum = path.with_name(path.name + ".sha256").read_text(encoding="utf-8").strip().split()
    require(checksum == [expected_hash, "latest.zip"], "Runtime ZIP checksum mismatch")
    with ZipFile(path) as archive:
        items = archive.infolist()
        names = [item.filename for item in items]
        require(len(set(names)) == len(names), "Duplicate ZIP entry")
        require(sum(item.file_size for item in items) < 512 * 1024 * 1024, "Unexpected expanded ZIP size")
        for item in items:
            name = item.orig_filename
            relative = PurePosixPath(name)
            require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in name and ":" not in name and "\0" not in name,
                    "Unsafe ZIP entry path")
            require(not name.lower().endswith((".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm")), "User database in distribution")
        require(archive.testzip() is None, "Runtime ZIP failed its CRC check")
        for required in ("PlayerTrackEnhanced.dll", "PlayerTrackEnhanced.json", "LICENSE", "THIRD_PARTY_NOTICES.md", "LICENSES/PeepingTom-EUPL-1.2.txt"):
            require(required in names, f"Missing runtime file: {required}")
        manifest = json.loads(archive.read("PlayerTrackEnhanced.json"))
        for key in ("InternalName", "AssemblyVersion", "DalamudApiLevel"):
            require(manifest.get(key) == entry.get(key), f"Embedded manifest disagrees with repo.json: {key}")
    if previous_root is not None and (previous_root / "repo.json").is_file():
        previous, _ = release_info(previous_root, repository, branch, legacy=True)
        require(version_key(entry["AssemblyVersion"]) >= version_key(previous["AssemblyVersion"]), "Version downgrade rejected")
        existing = previous_root / path.relative_to(root)
        if existing.exists():
            require(payload_digest(existing) == payload_digest(path), "Published version is immutable; increase the plugin version")
    return {"version": entry["AssemblyVersion"], "sha256": expected_hash, "runtime": str(path)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repository", default="cloudesh/ptenhanced")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--previous-root", type=Path)
    parser.add_argument("--same-payload", type=Path, nargs=2, metavar=("OLD", "NEW"))
    args = parser.parse_args()
    try:
        if args.same_payload:
            require(payload_digest(args.same_payload[0]) == payload_digest(args.same_payload[1]), "Published version is immutable; increase the plugin version")
        else:
            result = validate(args.root, args.repository, args.branch, args.previous_root)
            print(f"Validated PlayerTrack {result['version']} · SHA-256 {result['sha256']}")
    except (ValueError, OSError, KeyError, BadZipFile) as error:
        parser.exit(1, f"Release validation failed: {error}\n")
