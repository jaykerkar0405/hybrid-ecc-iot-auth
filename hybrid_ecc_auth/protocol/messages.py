"""Wire-format (de)serialization for M1/M2, with a versioned schema.

The protocol core is transport-agnostic (Section 4.3 of the PRD): this
module turns Message1/Message2 into a self-contained JSON blob (binary
fields base64-encoded) and back. Framing (e.g. length-prefixing for a raw
TCP stream) is a transport concern and lives in demo/, not here.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

#: Bumped on any incompatible change to the M1/M2 field layout.
PROTOCOL_VERSION = 1


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


class MessageFormatError(ValueError):
    """Raised when a wire blob is not a valid, version-compatible message."""


@dataclass(frozen=True)
class Message1:
    """Device -> Server (Eq. 15): M1 = <PID_{Vi,t}, C1, mu_1>."""

    pid: bytes
    gcm_nonce: bytes
    ciphertext: bytes
    tag: bytes  # mu_1

    def to_bytes(self) -> bytes:
        payload = {
            "v": PROTOCOL_VERSION,
            "type": "M1",
            "pid": _b64(self.pid),
            "nonce": _b64(self.gcm_nonce),
            "ct": _b64(self.ciphertext),
            "tag": _b64(self.tag),
        }
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message1":
        try:
            payload = json.loads(data.decode("utf-8"))
            if payload.get("type") != "M1":
                raise MessageFormatError(f"expected type M1, got {payload.get('type')!r}")
            if payload.get("v") != PROTOCOL_VERSION:
                raise MessageFormatError(f"unsupported protocol version {payload.get('v')!r}")
            return cls(
                pid=_unb64(payload["pid"]),
                gcm_nonce=_unb64(payload["nonce"]),
                ciphertext=_unb64(payload["ct"]),
                tag=_unb64(payload["tag"]),
            )
        except MessageFormatError:
            raise
        except Exception as exc:  # noqa: BLE001 - deliberately wraps any parse failure
            raise MessageFormatError(f"malformed M1 payload: {exc}") from exc


@dataclass(frozen=True)
class Message2:
    """Server -> Device (Eq. 19): M2 = <ID_Rj or PID_{Rj,t}, C2, sigma_2>."""

    server_id: str
    gcm_nonce: bytes
    ciphertext: bytes
    tag: bytes  # sigma_2

    def to_bytes(self) -> bytes:
        payload = {
            "v": PROTOCOL_VERSION,
            "type": "M2",
            "sid": self.server_id,
            "nonce": _b64(self.gcm_nonce),
            "ct": _b64(self.ciphertext),
            "tag": _b64(self.tag),
        }
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message2":
        try:
            payload = json.loads(data.decode("utf-8"))
            if payload.get("type") != "M2":
                raise MessageFormatError(f"expected type M2, got {payload.get('type')!r}")
            if payload.get("v") != PROTOCOL_VERSION:
                raise MessageFormatError(f"unsupported protocol version {payload.get('v')!r}")
            return cls(
                server_id=payload["sid"],
                gcm_nonce=_unb64(payload["nonce"]),
                ciphertext=_unb64(payload["ct"]),
                tag=_unb64(payload["tag"]),
            )
        except MessageFormatError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise MessageFormatError(f"malformed M2 payload: {exc}") from exc
