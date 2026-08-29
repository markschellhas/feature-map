# Draft Homebrew formula. Fill url/sha256 from the PyPI sdist after the
# first upload. Full steps: PUBLISH.md.
#
# Until then, install from this tree:
#
#   pip install -e .
#
# or from a tap:
#
#   brew install --HEAD markschellhas/tap/feature-map

class FeatureMap < Formula
  desc "Cross-app architecture research CLI"
  homepage "https://github.com/markschellhas/feature-map"
  license "MIT"
  head "https://github.com/markschellhas/feature-map.git", branch: "master"

  depends_on "python@3.12"

  def install
    virtualenv = libexec/"venv"
    system Formula["python@3.12"].opt_libexec/"bin/python", "-m", "venv", virtualenv
    system virtualenv/"bin/pip", "install", "."
    bin.install_symlink virtualenv/"bin/feature-map"
    (share/"feature-map").install Dir["share/feature_map/*"] if File.directory?("share/feature_map")
  end

  test do
    assert_match "1.0.0", shell_output("#{bin}/feature-map --version")
  end
end
