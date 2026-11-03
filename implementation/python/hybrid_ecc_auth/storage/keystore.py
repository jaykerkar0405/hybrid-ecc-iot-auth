"""Local, demo-grade credential storage.

NON-PRODUCTION CAVEAT (PRD Section 7.3): this is file-based storage
protected only by OS-level file permissions (0600 on POSIX). It is NOT
equivalent to a hardware security module or secure element and MUST NOT be
used to store real secrets.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from ..protocol.ta import Credential

#: Owner read/write only.
_PRIVATE_FILE_MODE = 0o600


class KeyStore:
    """A single credential bundle persisted to one JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, credential: Credential) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(credential.to_dict()).encode("utf-8")

        # Create (or truncate) with restrictive permissions from the start,
        # rather than chmod-ing after the fact (avoids a brief window where
        # the file exists with default, broader permissions).
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _PRIVATE_FILE_MODE)
        try:
            os.write(fd, payload)
        finally:
            os.close(fd)
        os.chmod(self.path, _PRIVATE_FILE_MODE)

    def load(self) -> Credential:
        mode = self.path.stat().st_mode
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            # Group/other permissions crept in (e.g. restored from an
            # archive) -- tighten before reading rather than silently
            # trusting a world-readable secret file.
            os.chmod(self.path, _PRIVATE_FILE_MODE)
        data = json.loads(self.path.read_bytes())
        return Credential.from_dict(data)

    def exists(self) -> bool:
        return self.path.exists()
