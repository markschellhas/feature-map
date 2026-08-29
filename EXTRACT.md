# Extract this package to its own GitHub repository

Packaging, PyPI, and Homebrew steps after the split: [GUIDE.md §2](GUIDE.md#2-how-to-package-it-so-anybody-can-use-it).


`feature-map` is a complete, independently versioned Python package. It has no
imports from playbook-app. Map data (`.features/*.yaml`) stays in each consumer
repo, including playbook-app.

Cloud Agent GitHub tokens cannot call `createRepository`. Create the empty
remote once, then split:

```bash
# 1. Create the empty public repo in the GitHub UI:
#    https://github.com/new  →  markschellhas/feature-map

# 2. Split this directory into its own history
cd /path/to/playbook-app
git subtree split --prefix=featuremap -b featuremap-split

# 3. Push that history to the new remote
git push git@github.com:markschellhas/feature-map.git featuremap-split:main
```

After the first push:

```bash
git clone git@github.com:markschellhas/feature-map.git
cd feature-map
pip install -e ".[dev]"
python -m pytest -q
```

Homebrew: publish a tag (`v1.0.0`), fill `sha256` in `Formula/feature-map.rb`,
and add the formula to a tap (for example `homebrew-taptics` or a personal tap).

playbook-app can keep using `./bin/feature-map` until the team switches to
`brew install feature-map` / `pip install feature-map` and a PATH shim.
