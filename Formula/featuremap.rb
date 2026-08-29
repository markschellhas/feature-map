# Draft Homebrew formula. Point url/sha256 at a GitHub release tag once
# markschellhas/featuremap exists. Until then, install from this tree:
#
#   pip install -e .
#
# or from git after the standalone repo is published:
#
#   brew install --HEAD markschellhas/tap/featuremap

class Featuremap < Formula
  desc "Cross-app architecture research CLI"
  homepage "https://github.com/markschellhas/featuremap"
  license "MIT"
  head "https://github.com/markschellhas/featuremap.git", branch: "main"

  depends_on "python@3.12"

  def install
    virtualenv = libexec/"venv"
    system Formula["python@3.12"].opt_libexec/"bin/python", "-m", "venv", virtualenv
    system virtualenv/"bin/pip", "install", "."
    bin.install_symlink virtualenv/"bin/featuremap"
    (share/"featuremap").install Dir["share/featuremap/*"] if File.directory?("share/featuremap")
  end

  test do
    assert_match "1.0.0", shell_output("#{bin}/featuremap --version")
  end
end
