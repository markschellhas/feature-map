.PHONY: test install npm-check

install:
	python3 -m pip install -e ".[dev]"

test:
	PYTHONPATH=src:tests python3 -m pytest -q

npm-check:
	node --check bin/feature-map.js
	node --check scripts/postinstall.js
	node --check scripts/python.js
