import pytest
from pathlib import Path
from ppa_publish.config import PPAConfig, load_config, ConfigError


def test_load_valid_config(tmp_path):
    """Test loading a valid .ppa-publish.yml file"""
    config_file = tmp_path / ".ppa-publish.yml"
    config_file.write_text("""
package:
  name: test-package
  description: Test package
  section: utils
  license: MIT
  homepage: https://github.com/test/repo

maintainer:
  name: Test User
  email: test@example.com

ppa:
  username: testuser
  ppa_name: test-ppa

releases:
  - noble
  - jammy

dependencies:
  build:
    - debhelper (>= 10)
  runtime:
    - bash (>= 4.0)

install:
  - source: bin/test.sh
    dest: usr/bin/
""")

    config = load_config(config_file)

    assert config.package.name == "test-package"
    assert config.package.section == "utils"
    assert config.maintainer.email == "test@example.com"
    assert len(config.releases) == 2
    assert "noble" in config.releases


def test_load_missing_config():
    """Test loading non-existent config raises error"""
    with pytest.raises(ConfigError, match="not found"):
        load_config(Path("/nonexistent/.ppa-publish.yml"))


def test_load_invalid_yaml(tmp_path):
    """Test loading invalid YAML raises error"""
    config_file = tmp_path / ".ppa-publish.yml"
    config_file.write_text("invalid: yaml: content:")

    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(config_file)
