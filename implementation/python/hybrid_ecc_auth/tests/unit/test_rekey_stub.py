"""FR-8.1: the v2 rekey stub must exist and clearly refuse to run, rather
than silently doing nothing."""

from __future__ import annotations

import pytest

from hybrid_ecc_auth.protocol.rekey import rekey


def test_rekey_stub_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        rekey()
