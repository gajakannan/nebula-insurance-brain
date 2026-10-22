"""Prove schemas work from the built wheel with repository fallback disabled."""
import hashlib
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

wheel = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(wheel))
import brain_content
from brain_content.contracts import schema

assert ".whl/" in brain_content.__file__
with zipfile.ZipFile(wheel) as archive:
    names = sorted(name for name in archive.namelist() if "/schemas/" in name)
    assert len(names) == 5
    with patch.object(Path, "is_file", return_value=False):
        for name in names:
            assert schema(name.rsplit("/", 1)[1])["$schema"]
print(f"Packaged schema proof PASS: 5 contracts; wheel sha256={hashlib.sha256(wheel.read_bytes()).hexdigest()}")

