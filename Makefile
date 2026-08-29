.PHONY: test install

install:
	python3 -m pip install -e ".[dev]"

test:
	PYTHONPATH=src:tests python3 -m pytest -q
