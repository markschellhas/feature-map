class FeatureMap < Formula
  include Language::Python::Virtualenv

  desc "Cross-app architecture research CLI"
  homepage "https://github.com/markschellhas/feature-map"
  url "https://files.pythonhosted.org/packages/70/cc/b644d027df1838cf426108ca851e954daa8630c7101e42efa04c59230bb1/feature_map_cli-1.1.0.tar.gz"
  sha256 "558561268959b702521b8a904fabe15ad3203dc7083326a4f4bdca611c56a914"
  license "MIT"
  head "https://github.com/markschellhas/feature-map.git", branch: "master"

  depends_on "libyaml"
  depends_on "python@3.12"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz"
    sha256 "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/feature-map --version")
  end
end
