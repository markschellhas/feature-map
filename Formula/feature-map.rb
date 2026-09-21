class FeatureMap < Formula
  include Language::Python::Virtualenv

  desc "Cross-app architecture research CLI"
  homepage "https://github.com/markschellhas/feature-map"
  url "https://files.pythonhosted.org/packages/34/9b/4657b469ed4ea5a11a22ed9c5ef8a78923ccd98f3cab33c19514114c82dd/feature_map_cli-1.2.6.tar.gz"
  sha256 "9aea32c82cc95730295f4a10a02644baee4ee84301d37fea309b98bb699faa03"
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
