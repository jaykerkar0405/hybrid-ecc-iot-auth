# `make reproduce` runs the same pipeline as run_all.sh (which is the tested path on Windows/Git Bash).
reproduce:
	bash run_all.sh
test:
	.venv/bin/python -m pytest -q tests || .venv/Scripts/python -m pytest -q tests
.PHONY: reproduce test
