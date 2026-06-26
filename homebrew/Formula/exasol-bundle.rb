class ExasolBundle < Formula
  include Language::Python::Virtualenv

  desc "Universal orchestrator for the Exasol tooling ecosystem"
  homepage "https://github.com/exasol/exa-bundle"
  
  # Replace URL with the actual link to your .tar.gz on PyPI
  url "https://files.pythonhosted.org/packages/source/e/exasol-bundle/exasol-bundle-1.0.18.tar.gz"
  # TODO: Before publishing, compute the real hash with:
  #   shasum -a 256 exasol-bundle-1.0.18.tar.gz
  # Then replace the placeholder below with the actual digest.
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  
  license "MIT"

  depends_on "python@3.11"

  def install
    # Creates an isolated Python virtual environment inside Homebrew
    virtualenv_install_with_resources
  end

  def post_install
    # Automatically initialize after brew finishes downloading
    system "#{bin}/exa-bundle", "init"
  end

  test do
    assert_match "Exasol Universal Bundler", shell_output("#{bin}/exa-bundle --help")
  end
end