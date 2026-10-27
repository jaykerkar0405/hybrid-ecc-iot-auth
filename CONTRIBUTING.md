# Contributing

1. Set up: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev,bench]"`
2. Run the tests before opening a PR: `pytest hybrid_ecc_auth/tests/ -q`
3. CI requires at least 90% coverage on `protocol/` and `crypto/`.
4. Keep field names close to the paper's notation so code stays traceable to its equations (see `docs/design.md`).
5. Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `research:`, `test:`).
6. Do not commit credentials, `creds/`, `manifest.json` or `firmware/esp8266/include/config.h`.
