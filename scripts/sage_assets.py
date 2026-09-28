#!/usr/bin/env python3
"""Pack, recover, fetch, and publish Sage authoring assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import zipfile


REPOSITORY = "zaratanDotWorld/models"
RELEASE_TAG = "sage-assets"
ARCHIVE_PREFIX = "sage-assets-"
BUNDLE_METADATA = "sage-assets-bundle.json"
MASTER = "properties/sage/sage.blend"
FURNITURE = ".local/sage-furniture-unbatched.glb"
TEXTURE_ROOT = "properties/sage/textures/"
TEXTURE_SUFFIXES = {
    ".exr", ".hdr", ".jpeg", ".jpg", ".ktx2", ".png", ".tif", ".tiff", ".webp"
}


class AssetError(RuntimeError):
    """A safe, user-facing asset workflow failure."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetError(f"Cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssetError(f"Expected a JSON object in {path}")
    return value


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(_json_bytes(value))
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _supported_payload(path: str) -> bool:
    if path in {MASTER, FURNITURE}:
        return True
    return path.startswith(TEXTURE_ROOT) and Path(path).suffix.lower() in TEXTURE_SUFFIXES


def _payload_paths(root: Path) -> list[str]:
    paths = [MASTER, FURNITURE]
    texture_dir = root / TEXTURE_ROOT
    if not texture_dir.is_dir():
        raise AssetError(f"Missing texture directory: {texture_dir}")
    paths.extend(
        path.relative_to(root).as_posix()
        for path in sorted(texture_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in TEXTURE_SUFFIXES
    )
    if len(paths) == 2:
        raise AssetError(f"No texture binaries found in {texture_dir}")
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise AssetError(f"Expected a regular payload file: {path}")
    return paths


def _content_hash(payloads: list[dict]) -> str:
    identity = [
        {"path": item["path"], "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in payloads
    ]
    return _sha256_bytes(json.dumps(identity, separators=(",", ":"), sort_keys=True).encode())


def _validate_payload_inventory(payloads: object) -> list[dict]:
    if not isinstance(payloads, list):
        raise AssetError("Manifest payload inventory is invalid")
    paths = []
    for item in payloads:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise AssetError("Manifest payload entry is invalid")
        path, size, digest = item["path"], item["bytes"], item["sha256"]
        if not isinstance(path, str):
            raise AssetError("Manifest payload path is invalid")
        _validate_relative_path(path)
        if (
            not _supported_payload(path)
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise AssetError(f"Manifest payload entry is invalid: {path}")
        paths.append(path)
    if len(paths) != len(set(paths)) or MASTER not in paths or FURNITURE not in paths:
        raise AssetError("Manifest payload inventory is incomplete or duplicated")
    if not any(path.startswith(TEXTURE_ROOT) for path in paths):
        raise AssetError("Manifest payload inventory contains no texture binaries")
    return payloads


def _source_provenance(root: Path) -> dict:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AssetError(f"Cannot record Git source provenance: {exc}") from exc
    return {"revision": revision, "worktree_dirty": dirty}


def pack(root: Path, output_dir: Path) -> tuple[Path, Path, dict]:
    root = root.absolute()
    output_dir = output_dir.absolute()
    payloads = []
    for relative in _payload_paths(root):
        path = root / relative
        payloads.append({"path": relative, "bytes": path.stat().st_size, "sha256": _sha256_file(path)})

    metadata = {
        "format_version": 1,
        "content_sha256": _content_hash(payloads),
        "payloads": payloads,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".sage-assets-", suffix=".zip", dir=output_dir)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, data in [(BUNDLE_METADATA, _json_bytes(metadata))] + [
                (item["path"], (root / item["path"]).read_bytes()) for item in payloads
            ]:
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, data, compresslevel=9)
        archive_sha256 = _sha256_file(temporary)
        archive_name = f"{ARCHIVE_PREFIX}{archive_sha256}.zip"
        archive_path = output_dir / archive_name
        if archive_path.exists():
            if _sha256_file(archive_path) != archive_sha256:
                raise AssetError(f"Existing archive has unexpected bytes: {archive_path}")
            temporary.unlink()
        else:
            os.replace(temporary, archive_path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    bundle = {
        "archive_name": archive_name,
        "archive_sha256": archive_sha256,
        "content_sha256": metadata["content_sha256"],
        "payloads": payloads,
        "source": _source_provenance(root),
    }
    candidate = {
        "format_version": 1,
        "repository": REPOSITORY,
        "release": {"tag": RELEASE_TAG, "prerelease": True},
        "candidate": bundle,
    }
    candidate_path = output_dir / "candidate.json"
    _write_json(candidate_path, candidate)
    return archive_path, candidate_path, candidate


def _validate_relative_path(name: str) -> None:
    pure = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() != name
    ):
        raise AssetError(f"Unsafe archive path: {name!r}")


def validate_archive(path: Path, expected_sha256: str | None = None) -> tuple[dict, dict[str, bytes]]:
    if expected_sha256 and _sha256_file(path) != expected_sha256:
        raise AssetError(f"Archive SHA-256 does not match the manifest: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise AssetError("Archive contains duplicate paths")
            for info in infos:
                _validate_relative_path(info.filename)
                mode = info.external_attr >> 16
                if info.is_dir() or stat.S_ISLNK(mode):
                    raise AssetError(f"Archive contains a directory or link: {info.filename}")
            if BUNDLE_METADATA not in names:
                raise AssetError(f"Archive is missing {BUNDLE_METADATA}")
            try:
                metadata = json.loads(archive.read(BUNDLE_METADATA))
            except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise AssetError(f"Invalid archive metadata: {exc}") from exc
            payloads = metadata.get("payloads") if isinstance(metadata, dict) else None
            if not isinstance(metadata, dict) or metadata.get("format_version") != 1:
                raise AssetError("Unsupported archive metadata")
            _validate_payload_inventory(payloads)
            declared = []
            data_by_path = {}
            for item in payloads:
                if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
                    raise AssetError("Invalid payload entry in archive metadata")
                relative = item["path"]
                if not isinstance(relative, str):
                    raise AssetError("Invalid payload path in archive metadata")
                _validate_relative_path(relative)
                if not _supported_payload(relative):
                    raise AssetError(f"Unsupported payload path: {relative}")
                try:
                    data = archive.read(relative)
                except KeyError as exc:
                    raise AssetError(f"Archive is missing declared payload: {relative}") from exc
                if len(data) != item["bytes"] or _sha256_bytes(data) != item["sha256"]:
                    raise AssetError(f"Payload does not match archive metadata: {relative}")
                declared.append(relative)
                data_by_path[relative] = data
            if set(names) != {BUNDLE_METADATA, *declared}:
                raise AssetError("Archive contains undeclared files")
            if len(declared) != len(set(declared)) or MASTER not in declared or FURNITURE not in declared:
                raise AssetError("Archive payload inventory is incomplete or duplicated")
            if not any(name.startswith(TEXTURE_ROOT) for name in declared):
                raise AssetError("Archive contains no texture binaries")
            if metadata.get("content_sha256") != _content_hash(payloads):
                raise AssetError("Archive content identity does not match its payload inventory")
            return metadata, data_by_path
    except (OSError, zipfile.BadZipFile) as exc:
        raise AssetError(f"Cannot read archive {path}: {exc}") from exc


def _bundle_from_manifest(manifest: dict, selection: str) -> dict:
    _validate_manifest_identity(manifest)
    key = "candidate" if selection == "candidate" else selection
    bundle = manifest.get(key)
    if not isinstance(bundle, dict):
        raise AssetError(f"Manifest has no {selection} bundle")
    required = {"archive_name", "archive_sha256", "content_sha256", "payloads"}
    if not required.issubset(bundle):
        raise AssetError(f"Manifest {selection} bundle is incomplete")
    archive_sha256 = bundle["archive_sha256"]
    content_sha256 = bundle["content_sha256"]
    if (
        not isinstance(archive_sha256, str)
        or len(archive_sha256) != 64
        or any(character not in "0123456789abcdef" for character in archive_sha256)
        or bundle["archive_name"] != f"{ARCHIVE_PREFIX}{archive_sha256}.zip"
        or not isinstance(content_sha256, str)
        or len(content_sha256) != 64
        or any(character not in "0123456789abcdef" for character in content_sha256)
    ):
        raise AssetError(f"Manifest {selection} bundle identity is invalid")
    _validate_payload_inventory(bundle["payloads"])
    if _content_hash(bundle["payloads"]) != content_sha256:
        raise AssetError(f"Manifest {selection} bundle identity is invalid")
    return bundle


def _validate_manifest_identity(manifest: dict) -> None:
    if manifest.get("format_version") != 1:
        raise AssetError("Unsupported manifest format")
    release = manifest.get("release")
    if (
        manifest.get("repository") != REPOSITORY
        or not isinstance(release, dict)
        or release.get("tag") != RELEASE_TAG
        or release.get("prerelease") is not True
    ):
        raise AssetError("Manifest identifies a different repository or release")


def _check_destination(root: Path, relative: str) -> Path:
    destination = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    if current.is_symlink():
        raise AssetError(f"Recovery destination is a symlink: {current}")
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        if current.is_symlink():
            raise AssetError(f"Recovery path traverses a symlink: {current}")
    if destination.is_symlink():
        raise AssetError(f"Recovery file is a symlink: {destination}")
    return destination


def recover(archive_path: Path, bundle: dict, destination: Path, force: bool = False) -> None:
    metadata, data_by_path = validate_archive(archive_path, bundle["archive_sha256"])
    if metadata["content_sha256"] != bundle["content_sha256"] or metadata["payloads"] != bundle["payloads"]:
        raise AssetError("Archive payload inventory does not match the selected manifest")

    destination = destination.absolute()
    if destination.exists() and not destination.is_dir():
        raise AssetError(f"Recovery destination is not a directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    writes = []
    for relative, data in data_by_path.items():
        path = _check_destination(destination, relative)
        if path.exists():
            if not path.is_file():
                raise AssetError(f"Recovery target is not a regular file: {path}")
            existing = path.read_bytes()
            if existing == data:
                continue
            if not force:
                raise AssetError(f"Refusing to overwrite differing local asset: {path}")
            writes.append((path, data, existing))
        else:
            writes.append((path, data, None))

    completed = []
    try:
        for path, data, previous in writes:
            path.parent.mkdir(parents=True, exist_ok=True)
            _check_destination(destination, path.relative_to(destination).as_posix())
            fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            try:
                with os.fdopen(fd, "wb") as output:
                    output.write(data)
                os.replace(temporary, path)
            except BaseException:
                Path(temporary).unlink(missing_ok=True)
                raise
            completed.append((path, previous))
    except BaseException:
        for path, previous in reversed(completed):
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous)
        raise


def _run_gh(arguments: list[str], cwd: Path | None = None, allow_failure: bool = False) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(["gh", *arguments], cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
        raise AssetError(f"Cannot run GitHub CLI: {exc}") from exc
    if result.returncode and not allow_failure:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise AssetError(f"GitHub CLI failed: gh {' '.join(arguments)}: {detail}")
    return result


def _release_view(repository: str, tag: str) -> dict | None:
    result = _run_gh(
        ["release", "view", tag, "--repo", repository, "--json", "tagName,isPrerelease,isImmutable,assets"],
        allow_failure=True,
    )
    if result.returncode:
        message = (result.stderr + result.stdout).lower()
        if "release not found" in message or "not found" in message:
            return None
        raise AssetError(f"Cannot inspect GitHub release: {result.stderr.strip() or result.stdout.strip()}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssetError(f"GitHub CLI returned invalid release JSON: {exc}") from exc
    return value


def _download(repository: str, tag: str, archive_name: str, directory: Path) -> Path:
    _run_gh(
        ["release", "download", tag, "--repo", repository, "--pattern", archive_name, "--dir", str(directory)]
    )
    path = directory / archive_name
    if not path.is_file():
        raise AssetError(f"GitHub CLI did not download {archive_name}")
    return path


def fetch(manifest_path: Path, selection: str, destination: Path, force: bool = False) -> None:
    manifest = _read_json(manifest_path)
    bundle = _bundle_from_manifest(manifest, selection)
    with tempfile.TemporaryDirectory(prefix="sage-assets-fetch-") as temporary:
        archive = _download(manifest["repository"], manifest["release"]["tag"], bundle["archive_name"], Path(temporary))
        recover(archive, bundle, destination, force)


def _prune(repository: str, tag: str, assets: list[dict], keep: set[str]) -> None:
    for asset in assets:
        name = asset.get("name") if isinstance(asset, dict) else None
        if (
            isinstance(name, str)
            and name.startswith(ARCHIVE_PREFIX)
            and name.endswith(".zip")
            and len(name) == len(ARCHIVE_PREFIX) + 64 + 4
            and all(character in "0123456789abcdef" for character in name[len(ARCHIVE_PREFIX):-4])
            and name not in keep
        ):
            _run_gh(["release", "delete-asset", tag, name, "--repo", repository, "--yes"])


def _workflow_asset_names(release: dict) -> set[str]:
    names = set()
    for asset in release.get("assets", []):
        name = asset.get("name") if isinstance(asset, dict) else None
        if (
            isinstance(name, str)
            and name.startswith(ARCHIVE_PREFIX)
            and name.endswith(".zip")
            and len(name) == len(ARCHIVE_PREFIX) + 64 + 4
            and all(character in "0123456789abcdef" for character in name[len(ARCHIVE_PREFIX):-4])
        ):
            names.add(name)
    return names


def _check_release_state(release: dict, current: dict | None, previous: dict | None, candidate: dict) -> set[str]:
    workflow_assets = _workflow_asset_names(release)
    represented = {candidate["archive_name"]}
    represented.update(
        bundle["archive_name"] for bundle in (current, previous) if isinstance(bundle, dict)
    )
    if workflow_assets - represented:
        raise AssetError("Release contains bundles not represented by the published manifest or candidate")
    if isinstance(current, dict) and current["archive_name"] not in workflow_assets:
        raise AssetError("Published manifest's current archive is missing from the release")
    return workflow_assets


def publish(candidate_path: Path, manifest_path: Path) -> None:
    candidate = _read_json(candidate_path)
    bundle = _bundle_from_manifest(candidate, "candidate")
    archive_path = candidate_path.parent / bundle["archive_name"]
    metadata, _ = validate_archive(archive_path, bundle["archive_sha256"])
    if metadata["content_sha256"] != bundle["content_sha256"] or metadata["payloads"] != bundle["payloads"]:
        raise AssetError("Local archive does not match the candidate manifest")
    repository = candidate["repository"]
    tag = candidate["release"]["tag"]

    published = _read_json(manifest_path)
    _validate_manifest_identity(published)
    current = published.get("current")
    previous = published.get("previous")
    if current is not None:
        current = _bundle_from_manifest(published, "current")
    if previous is not None:
        previous = _bundle_from_manifest(published, "previous")
    if isinstance(current, dict) and current.get("content_sha256") == bundle["content_sha256"]:
        release = _release_view(repository, tag)
        if release is None:
            raise AssetError("Published manifest points to a release that does not exist")
        _check_release_state(release, current, previous, bundle)
        with tempfile.TemporaryDirectory(prefix="sage-assets-current-") as temporary:
            downloaded = _download(repository, tag, current["archive_name"], Path(temporary))
            metadata, _ = validate_archive(downloaded, current["archive_sha256"])
            if metadata["content_sha256"] != current["content_sha256"] or metadata["payloads"] != current["payloads"]:
                raise AssetError("Downloaded current archive does not match the published manifest")
        _prune(repository, tag, release.get("assets", []), {
            item["archive_name"] for item in (current, previous) if isinstance(item, dict)
        })
        print(f"Already published: {current['archive_name']}")
        return

    release = _release_view(repository, tag)
    if release is None:
        source = bundle.get("source", {})
        revision = source.get("revision")
        if not isinstance(revision, str) or not revision:
            raise AssetError("Candidate lacks a Git source revision for release creation")
        _run_gh([
            "release", "create", tag,
            "--repo", repository,
            "--title", "Sage authoring assets",
            "--notes", "Recoverable Sage Blender authoring assets.",
            "--target", revision,
            "--prerelease",
            "--latest=false",
        ])
        release = _release_view(repository, tag)
        if release is None:
            raise AssetError("GitHub release was not visible after creation")
    if release.get("isImmutable"):
        raise AssetError(f"Release {tag} is immutable")
    if not release.get("isPrerelease"):
        raise AssetError(f"Release {tag} must remain a prerelease")

    workflow_assets = _check_release_state(release, current, previous, bundle)
    if bundle["archive_name"] not in workflow_assets:
        _run_gh(["release", "upload", tag, str(archive_path), "--repo", repository])

    with tempfile.TemporaryDirectory(prefix="sage-assets-publish-") as temporary:
        downloaded = _download(repository, tag, bundle["archive_name"], Path(temporary))
        metadata, _ = validate_archive(downloaded, bundle["archive_sha256"])
        if metadata["content_sha256"] != bundle["content_sha256"] or metadata["payloads"] != bundle["payloads"]:
            raise AssetError("Downloaded archive does not match the candidate manifest")

    new_manifest = {
        "format_version": 1,
        "repository": repository,
        "release": {"tag": tag, "prerelease": True},
        "current": bundle,
        "previous": current if isinstance(current, dict) else None,
    }
    refreshed = _release_view(repository, tag)
    if refreshed is None:
        raise AssetError("Published release disappeared before retention cleanup")
    keep = {bundle["archive_name"]}
    if isinstance(current, dict):
        keep.add(current["archive_name"])
    _prune(repository, tag, refreshed.get("assets", []), keep)
    _write_json(manifest_path, new_manifest)
    print(f"Published and verified: {bundle['archive_name']}")


def _default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    root = _default_root()
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    pack_parser = subparsers.add_parser("pack", help="build a local candidate bundle")
    pack_parser.add_argument("--root", type=Path, default=root)
    pack_parser.add_argument("--output-dir", type=Path, default=root / ".local/sage-assets")

    recover_parser = subparsers.add_parser("recover", help="verify and recover a local candidate")
    recover_parser.add_argument("--candidate", type=Path, default=root / ".local/sage-assets/candidate.json")
    recover_parser.add_argument("--archive", type=Path)
    recover_parser.add_argument("--destination", type=Path, required=True)
    recover_parser.add_argument("--force", action="store_true")

    fetch_parser = subparsers.add_parser("fetch", help="download and recover a published bundle")
    fetch_parser.add_argument("--manifest", type=Path, default=root / "properties/sage/assets.json")
    fetch_parser.add_argument("--bundle", choices=("current", "previous"), default="current")
    fetch_parser.add_argument("--destination", type=Path, default=root)
    fetch_parser.add_argument("--force", action="store_true")

    publish_parser = subparsers.add_parser("publish", help="publish and verify the local candidate")
    publish_parser.add_argument("--candidate", type=Path, default=root / ".local/sage-assets/candidate.json")
    publish_parser.add_argument("--manifest", type=Path, default=root / "properties/sage/assets.json")

    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "pack":
            archive, candidate, _ = pack(arguments.root, arguments.output_dir)
            print(f"Archive: {archive}")
            print(f"Candidate manifest: {candidate}")
        elif arguments.command == "recover":
            candidate = _read_json(arguments.candidate)
            bundle = _bundle_from_manifest(candidate, "candidate")
            archive = arguments.archive or arguments.candidate.parent / bundle["archive_name"]
            recover(archive, bundle, arguments.destination, arguments.force)
            print(f"Recovered to: {arguments.destination.absolute()}")
        elif arguments.command == "fetch":
            fetch(arguments.manifest, arguments.bundle, arguments.destination, arguments.force)
            print(f"Recovered to: {arguments.destination.absolute()}")
        elif arguments.command == "publish":
            publish(arguments.candidate, arguments.manifest)
    except AssetError as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
