# Publish Feature Map to PyPI and Homebrew

This is the operator checklist for putting `feature-map` on the two install
paths people will actually use:

```bash
pip install feature-map
brew install markschellhas/tap/feature-map   # tap first; core later
```

Do PyPI first. Homebrew should install from the PyPI sdist (checksummed,
versioned) rather than `git HEAD`.

## Names — do not mix these up

| Surface | Name | Notes |
|---------|------|--------|
| pip / brew / CLI | `feature-map` | What you type |
| Python import | `feature_map` | Hyphens are illegal in module names |
| PyPI project | `feature-map` | Same project as `feature_map` (PEP 503) |
| **Not this project** | `featuremap` | [Existing PyPI package](https://pypi.org/project/featuremap/) (biology). `pip install featuremap` is the wrong thing. |

Confirm the name is still free before every first-time upload:

```bash
# should 404
curl -sI https://pypi.org/pypi/feature-map/json | head -1
```

A pending publisher on PyPI does **not** reserve the name. Someone else can
claim `feature-map` until your first successful upload.

---

## 0. Before either registry

1. GitHub repo is public: `https://github.com/markschellhas/feature-map`
2. Default branch is `master` (match the Homebrew `head` line and Actions)
3. Version is consistent in:
   - `pyproject.toml` → `[project].version`
   - `src/feature_map/_version.py` → `__version__`
   - `share/feature_map/skill/SKILL.md` frontmatter `version:`
   - `CHANGELOG.md` (move `[Unreleased]` into the tagged version)
4. Tests pass:

   ```bash
   pip install -e ".[dev]"
   python -m pytest -q
   feature-map --version    # must print the version you are tagging
   ```

5. Tag and GitHub release **after** PyPI is configured, not before. Tag
   format: `v1.0.0` (leading `v`).

---

## 1. PyPI

Recommended path: **Trusted Publishing** from GitHub Actions. No long-lived
API token in repo secrets. First upload can also create the project.

Manual `twine` is the fallback if you want to publish from your laptop.

### 1.1 Account

1. Create / sign in at [pypi.org](https://pypi.org/account/register/)
2. Enable 2FA (required to upload)
3. Same for [test.pypi.org](https://test.pypi.org/) if you want a dry run
   (separate account database)

### 1.2 Dry-run the artifacts locally

```bash
python3 -m pip install -U build twine
rm -rf dist
python3 -m build
python3 -m twine check dist/*
ls dist
# expect something like:
#   feature_map-1.0.0-py3-none-any.whl
#   feature_map-1.0.0.tar.gz
```

Hatchling normalizes the filename to `feature_map-…` even though the project
name is `feature-map`. That is correct.

Sanity-check the wheel:

```bash
python3 -m pip install dist/feature_map-*.whl
feature-map --version
python3 -c "import feature_map; print(feature_map.__version__)"
# confirm the other package was not involved:
python3 -c "import featuremap" 2>/dev/null && echo "WARNING: biology package also installed"
```

Uninstall when done: `pip uninstall -y feature-map`.

### 1.3 Trusted Publishing (preferred)

PyPI docs: [Creating a project with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

1. On GitHub: **Settings → Environments → New environment** named `pypi`.
   Add a required reviewer (you) so a tag cannot publish unattended.
2. On PyPI: account menu → **Publishing** (not a project page — the project
   does not exist yet).
3. Under GitHub, add a **pending** publisher:

   | Field | Value |
   |-------|--------|
   | PyPI project name | `feature-map` |
   | Owner | `markschellhas` |
   | Repository | `feature-map` |
   | Workflow name | `publish.yml` |
   | Environment | `pypi` |

4. Repeat on TestPyPI if you want a rehearsal (`test.pypi.org` → Publishing).
5. Add `.github/workflows/publish.yml` (see §1.5).
6. Commit, push, then:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

   Creating a GitHub Release from that tag also works if the workflow listens
   to `release: types: [published]`. The sample below listens to the tag.

7. Approve the `pypi` environment if GitHub asks. The first successful upload
   **creates** the PyPI project and converts the pending publisher into a
   normal one.

8. Confirm:

   ```bash
   pip index versions feature-map
   pip install feature-map
   feature-map --version
   ```

   Project page: `https://pypi.org/project/feature-map/`

If the pending publisher is never used, it does not hold the name. Upload
promptly after registering it.

### 1.4 Manual twine (fallback)

Create a **project-scoped** API token at PyPI → Account settings → API tokens.
For the first upload, PyPI only offers an account-wide token (`scope: entire
account`). After the project exists, revoke that token and mint one scoped to
`feature-map`.

```bash
# TestPyPI first
python3 -m twine upload --repository testpypi dist/*
pip install -i https://test.pypi.org/simple --extra-index-url https://pypi.org/simple feature-map

# Production
python3 -m twine upload dist/*
```

Username is `__token__`. Password is the token (`pypi-…`).

Do not commit the token. Do not use your PyPI password.

### 1.5 `publish.yml`

Save as `.github/workflows/publish.yml`. The filename must match the pending
publisher **Workflow name**.

```yaml
name: Publish

on:
  push:
    tags:
      - "v*"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: python -m pytest -q

  publish:
    needs: test
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/project/feature-map/
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -U build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

`id-token: write` is required. There is no `password:` / `PYPI_TOKEN` when
using Trusted Publishing.

To rehearse against TestPyPI, add `repository-url: https://test.pypi.org/legacy/`
to the publish action (or a second job with environment `testpypi`).

### 1.6 Later PyPI releases

1. Bump the four version sites in §0
2. Write the changelog
3. `git tag vX.Y.Z && git push origin vX.Y.Z`
4. Approve the environment
5. You cannot reuse a version. Yanked files still occupy that version number.

---

## 2. Homebrew

Ship a **personal tap** now. `homebrew/core` is a later submission: it wants a
stable tagged release, notability, and a formula that vendors Python
dependencies as checksummed `resource` blocks.

### 2.1 Fill the formula from the PyPI sdist

After PyPI has `1.0.0`:

```bash
curl -sL https://pypi.org/pypi/feature-map/json | python3 -c \
  "import json,sys; r=json.load(sys.stdin)['urls'];
[print(u['url'], u['digests']['sha256']) for u in r if u['packagetype']=='sdist']"
```

That URL and sha256 go on the formula. Example shape (replace the hash):

```ruby
class FeatureMap < Formula
  include Language::Python::Virtualenv

  desc "Cross-app architecture research CLI"
  homepage "https://github.com/markschellhas/feature-map"
  url "https://files.pythonhosted.org/packages/source/f/feature-map/feature_map-1.0.0.tar.gz"
  sha256 "REPLACE_ME"
  license "MIT"
  head "https://github.com/markschellhas/feature-map.git", branch: "master"

  depends_on "python@3.12"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/pyyaml-6.0.2.tar.gz"
    sha256 "REPLACE_ME"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/feature-map --version")
  end
end
```

`Formula/feature-map.rb` in this repo is a draft. Copy a completed formula into
the tap; keep a copy here only as a template.

Generate the `resource` block instead of hand-editing PyYAML:

```bash
brew update-python-resources --print-only --ignore-errors Formula/feature-map.rb
```

(`--ignore-errors` is for third-party taps when PyPI metadata is incomplete.)

`virtualenv_install_with_resources` creates a venv under `libexec`, installs
resources, installs the formula, and links `feature-map` into `bin`. Do not
`pip install` from the network in `def install` — Homebrew requires pinned
checksums.

### 2.2 Create the tap

A GitHub repo named `homebrew-tap` yields the short tap name `markschellhas/tap`.

```bash
brew tap-new markschellhas/homebrew-tap
cd "$(brew --repo markschellhas/tap)"
# paste the filled formula at Formula/feature-map.rb
git add Formula/feature-map.rb
git commit -m "feature-map 1.0.0"
gh repo create markschellhas/homebrew-tap --public --source=. --remote=origin --push
```

If you already have `homebrew-taptics`, put the formula there instead and
substitute `markschellhas/taptics` below.

### 2.3 Audit and install from the tap

```bash
brew audit --strict --online markschellhas/tap/feature-map
brew install --build-from-source markschellhas/tap/feature-map
feature-map --version
brew test markschellhas/tap/feature-map
```

Users then:

```bash
brew tap markschellhas/tap
brew install feature-map
# or one shot:
brew install markschellhas/tap/feature-map
```

`--HEAD` only for unreleased work:

```bash
brew install --HEAD markschellhas/tap/feature-map
```

### 2.4 Later tap releases

1. Publish the new version to PyPI
2. Update `url`, `sha256`, and the PyYAML `resource` if it moved
3. Commit on the tap: `feature-map 1.0.1`
4. `brew bump-formula-pr` is for core; on a tap you just push

### 2.5 `homebrew/core` (later)

Only after the tap is boring and the project has a real user base. Core
expects:

- A stable tagged release (not `--HEAD`)
- Licence DFSG-compatible (MIT is)
- No live `pip install` in `def install`
- Checksummed `resource`s for every Python dep
- Builds on the current macOS + Linux CI matrix
- [Notability / acceptable formulae](https://docs.brew.sh/Acceptable-Formulae)

Open a PR against [Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core)
with the same formula. Maintainers will bottle it. Until that lands, the
install command stays `brew install markschellhas/tap/feature-map`.

Do not submit to core on day one.

---

## 3. After both are live

Uncomment the real install lines in `README.md`:

```bash
pip install feature-map
brew install markschellhas/tap/feature-map
```

Keep the warning that `pip install featuremap` is a different project.

PyPI project metadata (description, homepage, license) comes from
`pyproject.toml` + `README.md` at upload time. To change it, cut a new
version; you cannot edit an already-uploaded file.

Optional: GitHub Release notes can copy `CHANGELOG.md` for that tag. The
PyPI page will already show the README.

---

## 4. Release checklist

- [ ] Version bumped in `pyproject.toml`, `_version.py`, skill frontmatter, changelog
- [ ] `pytest` green
- [ ] `python -m build && twine check dist/*`
- [ ] Pending publisher still valid **or** project already exists on PyPI
- [ ] Tag `vX.Y.Z` pushed; Actions publish job green
- [ ] `pip install feature-map` on a clean machine prints the new version
- [ ] Formula `url` / `sha256` / `resource` updated
- [ ] Tap commit pushed; `brew install --build-from-source` works
- [ ] README install lines match reality
