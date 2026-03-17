import pytest
from click.testing import CliRunner
from pathlib import Path
from ppa_publish.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def valid_project(tmp_path):
    config = tmp_path / ".ppa-publish.yml"
    config.write_text("""
package:
  name: test-package
  description: Test package
  section: utils
  license: MIT

maintainer:
  name: Test User
  email: test@example.com

ppa:
  username: testuser
  ppa_name: test-ppa

releases:
  - noble

dependencies:
  build:
    - debhelper (>= 10)
  runtime: []

install:
  - source: bin/test.sh
    dest: usr/bin/
""")

    (tmp_path / "bin").mkdir()
    script = tmp_path / "bin" / "test.sh"
    script.write_text("#!/bin/bash\necho 'test'\n")
    script.chmod(0o755)

    (tmp_path / "debian").mkdir()
    rules = tmp_path / "debian" / "rules"
    rules.write_text("#!/usr/bin/make -f\n\n%:\n\tdh $@\n")
    rules.chmod(0o755)

    return tmp_path


def test_validate_passes(runner, valid_project, monkeypatch):
    monkeypatch.chdir(valid_project)
    result = runner.invoke(cli, ['validate'])
    assert result.exit_code == 0


def test_validate_fails_missing_config(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, ['validate'])
    assert result.exit_code != 0
