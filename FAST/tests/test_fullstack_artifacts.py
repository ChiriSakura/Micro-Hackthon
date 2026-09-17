"""Check archive portability, tamper detection and evidence retention."""
import io
import json
from pathlib import Path
import tarfile

import pytest

from fast.fullstack.artifacts import create_archive, verify_archive


def test_archive_retains_failed_design_and_final_ppa_without_build_caches(tmp_path):
    run = tmp_path / "run"
    for name in ["failed/attempt.scala", "obj_dir/model.o", "summary.json",
                 "hammer/par-rundir/pre_extraction", "hammer/par-rundir/routed.odb",
                 "hammer/par-rundir/routed.v", "hammer/par-rundir/run.log"]:
        path = run / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
    archive = tmp_path / "evidence.tar.gz"
    result = create_archive({"run": run}, archive)
    files = result["manifest"]["files"]
    assert "run/failed/attempt.scala" in files
    assert "run/hammer/par-rundir/routed.odb" in files
    assert "run/hammer/par-rundir/run.log" in files
    assert not any("model.o" in f or "pre_extraction" in f for f in files)
    assert (run / "obj_dir/model.o").exists()  # archiving never deletes inputs
    with pytest.raises(FileExistsError):
        create_archive({"run": run}, archive)


def test_archive_detects_altered_member(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("original")
    result = create_archive({"source.txt": source}, tmp_path / "good.tar.gz")
    corrupt = tmp_path / "corrupt.tar.gz"
    with tarfile.open(corrupt, "w:gz") as archive:
        for name, data in [("source.txt", b"modified"),
                           ("artifact_manifest.json", json.dumps(result["manifest"]).encode())]:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    with pytest.raises(ValueError, match="integrity"):
        verify_archive(corrupt)


def test_archive_rejects_external_symlinks_and_nested_output(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (root / "external").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="regular file"):
        create_archive({"run": root}, tmp_path / "links.tar.gz")
    with pytest.raises(ValueError, match="inside an input"):
        create_archive({"run": root}, root / "recursive.tar.gz")
