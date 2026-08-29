# Draft Homebrew formula. Point url/sha256 at a GitHub release tag once
# a tap is published. Until then, install from this tree:
#
#   pip install -e .
#
# or from git after the standalone repo is published:
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
    (share/"feature-map").install Dir["share/featuremap/*"] if File.directory?("share/featuremap")
  end

  test do
    assert_match "1.0.0", shell_output("#{bin}/feature-map --version")
  end
end
