class FeatureMap < Formula
  include Language::Python::Virtualenv

  desc "Cross-app architecture research CLI"
  homepage "https://github.com/markschellhas/feature-map"
  url "https://files.pythonhosted.org/packages/e5/9f/4beb1fb9c7c21b925828c49f65443acc6f4c2627db6e712c2e3bfd25dc76/feature_map_cli-1.2.7.tar.gz"
  sha256 "bc7edc0206493c6724bf1a8d73dae108ffed51852a058caefb0679ea77690fad"
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
