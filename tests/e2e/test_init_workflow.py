import pytest
from click.testing import CliRunner
from pathlib import Path
from ppa_publish.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_init_creates_config_and_debian(runner, tmp_path, monkeypatch):
    """Test init command creates config and debian/ directory"""
    monkeypatch.chdir(tmp_path)

    inputs = [
        "test-package",
        "Test package description",
        "MIT",
        "https://github.com/test/repo",
        "Test User",
        "test@example.com",
        "testuser",
        "test-ppa",
        "noble,jammy",
        "y",  # confirm install of detected bash script
    ]

    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "test.sh").write_text("#!/bin/bash\necho 'test'\n")

    result = runner.invoke(cli, ['init'], input='\n'.join(inputs))

    assert result.exit_code == 0
    assert (tmp_path / ".ppa-publish.yml").exists()
    assert (tmp_path / "debian").is_dir()
    assert (tmp_path / "debian" / "changelog").exists()
