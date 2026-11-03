"""hea-ta: offline TA provisioning CLI (PRD Section 4.2, step 1).

Reads a manifest of entities to enroll, derives each lambda_X (Eq. 8) and
the pairwise peer-key lists (Section II model, FR-3.1) entirely locally --
no network I/O anywhere in this command, mirroring the paper's
"intrusion-free offline phase" -- and writes one credential bundle file
per entity.

Simplification (documented, not hidden): all entities that should be able
to mutually authenticate must appear together in one manifest / one
`enroll` invocation, since peer-key sharing (share_mutual_peer_keys) is
computed once, in-memory, at enrollment time. Re-running `enroll` with an
expanded manifest and the same --master-secret-hex is idempotent for
lambda derivation (Eq. 8 is deterministic) but will not retroactively
patch already-distributed bundles from an earlier, smaller run -- for
that, redistribute the freshly written bundles.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

from ..protocol.ta import TrustedAuthority
from ..storage.keystore import KeyStore

DEFAULT_MASTER_SECRET_FILENAME = "ta_master_secret.hex"


def _load_manifest(path: Path) -> list[dict]:
    entries = json.loads(path.read_text())
    if not isinstance(entries, list):
        raise ValueError("manifest must be a JSON array of {\"identity\": ..., \"role\": ...} objects")
    return entries


def _resolve_master_secret(out_dir: Path, master_secret_hex: str | None) -> bytes:
    if master_secret_hex:
        return bytes.fromhex(master_secret_hex)

    secret_path = out_dir / DEFAULT_MASTER_SECRET_FILENAME
    if secret_path.exists():
        print(f"Reusing existing TA master secret at {secret_path}", file=sys.stderr)
        return bytes.fromhex(secret_path.read_text().strip())

    secret = secrets.token_bytes(32)
    out_dir.mkdir(parents=True, exist_ok=True)
    secret_path.write_text(secret.hex())
    secret_path.chmod(0o600)
    print(
        f"Generated a new TA master secret and saved it to {secret_path} (0600). "
        "This file is TA-only and must never be distributed to devices/servers.",
        file=sys.stderr,
    )
    return secret


def cmd_enroll(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    manifest = _load_manifest(Path(args.manifest))
    master_secret = _resolve_master_secret(out_dir, args.master_secret_hex)

    ta = TrustedAuthority(master_secret=master_secret)
    try:
        creds = ta.enroll_batch(manifest)
    except (ValueError, KeyError) as exc:
        print(f"error: invalid manifest entry: {exc}", file=sys.stderr)
        return 2
    ta.share_mutual_peer_keys(list(creds.values()))

    out_dir.mkdir(parents=True, exist_ok=True)
    for identity, cred in creds.items():
        bundle_path = out_dir / f"{identity}.json"
        KeyStore(bundle_path).save(cred)
        print(f"Enrolled {identity!r} (role={cred.role}) -> {bundle_path}")

    print(f"\n{len(creds)} entities enrolled and cross-issued peer keys. Offline phase complete -- no network I/O occurred.")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hea-ta", description="Offline Trusted Authority provisioning (FR-2).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enroll = subparsers.add_parser("enroll", help="Enroll a batch of devices/servers from a manifest file.")
    enroll.add_argument("--manifest", required=True, help='JSON array of {"identity": ..., "role": "device"|"server"}.')
    enroll.add_argument("--out-dir", required=True, help="Directory to write per-entity credential bundles into.")
    enroll.add_argument(
        "--master-secret-hex",
        default=None,
        help="Reuse an existing TA master secret (hex). If omitted, one is generated (or reused from --out-dir).",
    )
    enroll.set_defaults(func=cmd_enroll)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
