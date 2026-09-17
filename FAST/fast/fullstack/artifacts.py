"""Portable experiment archives with a verified inventory and explicit exclusions.

This module never removes inputs. It preserves failed attempts and tool logs,
while excluding rebuildable caches and intermediate OpenROAD checkpoints.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile


CACHE_DIRECTORIES = frozenset({
    "obj_dir", ".scala-build", ".bsp", "scala_build", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
})


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return _stream_digest(stream)


def _stream_digest(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def exclusion_reason(path: Path) -> str | None:
    if any(part in CACHE_DIRECTORIES for part in path.parts):
        return "rebuildable compiler/simulator cache"
    if path.suffix in {".pyc", ".pyo"} or path.name == "core" or path.name.startswith("core.") and path.name[5:].isdigit():
        return "runtime cache or core dump"
    if path.parent.name == "par-rundir" and not path.suffix and (
        path.name.startswith(("pre_", "post_")) or path.name == "latest"
    ):
        return "intermediate OpenROAD checkpoint; final routed.odb retained"
    return None


def _safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and str(path) == name


def create_archive(inputs: dict[str, Path], output: Path) -> dict:
    """Archive named roots; reject symlinks rather than retain external dependencies."""
    if not inputs or any(not _safe_name(name) for name in inputs):
        raise ValueError("Archive inputs require safe relative names")
    roots = {name: path.resolve(strict=True) for name, path in inputs.items()}
    output = output.resolve()
    if any(path.is_dir() and output.is_relative_to(path) for path in roots.values()):
        raise ValueError("Archive output cannot be inside an input")
    inventory, excluded, files = {}, [], []
    for label, root in sorted(roots.items()):
        candidates = [root]
        if root.is_dir():
            candidates = []
            for directory, directories, names in os.walk(root, followlinks=False):
                for name in sorted(directories.copy()):
                    path = Path(directory) / name
                    relative = path.relative_to(root)
                    reason = exclusion_reason(relative)
                    if reason:
                        excluded.append({"path": f"{label}/{relative}", "reason": reason})
                        directories.remove(name)
                    elif path.is_symlink():
                        raise ValueError(f"Archive directory symlink is not portable: {path}")
                candidates.extend(Path(directory) / name for name in sorted(names))
        for path in candidates:
            name = label if root.is_file() else f"{label}/{path.relative_to(root)}"
            reason = exclusion_reason(Path(name))
            if reason:
                excluded.append({"path": name, "reason": reason})
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Archive input must be a regular file: {path}")
            if name in inventory or name == "artifact_manifest.json":
                raise ValueError(f"Duplicate/reserved archive member: {name}")
            inventory[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            files.append((name, path))
    manifest = {"version": 1, "inputs": {k: str(v) for k, v in roots.items()},
                "files": inventory, "excluded": excluded}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental replacement of published evidence.
    with output.open("xb") as destination:
        with tarfile.open(fileobj=destination, mode="w:gz", compresslevel=6) as archive:
            for name, path in files:
                archive.add(path, arcname=name, recursive=False)
            payload = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
            info = tarfile.TarInfo("artifact_manifest.json")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    # Re-read every archived byte. Input mutation during collection fails here.
    return verify_archive(output)


def verify_archive(path: Path) -> dict:
    """Verify member hashes without extracting or executing archive contents."""
    actual, manifest = {}, None
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            if not member.isfile() or not _safe_name(member.name):
                raise ValueError(f"Unsafe archive member: {member.name}")
            with archive.extractfile(member) as stream:
                if member.name == "artifact_manifest.json":
                    if manifest is not None:
                        raise ValueError("Duplicate archive manifest")
                    manifest = json.load(stream)
                else:
                    if member.name in actual:
                        raise ValueError(f"Duplicate archive member: {member.name}")
                    actual[member.name] = {"sha256": _stream_digest(stream), "bytes": member.size}
    if manifest is None or manifest.get("version") != 1 or actual != manifest.get("files"):
        raise ValueError("Archive integrity failed: member inventory/hash mismatch")
    return {"passed": True, "archive_sha256": sha256_file(path),
            "file_count": len(actual), "uncompressed_bytes": sum(v["bytes"] for v in actual.values()),
            "archive_bytes": path.stat().st_size, "manifest": manifest}
