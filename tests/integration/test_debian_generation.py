import pytest
from pathlib import Path
from ppa_publish.generators.debian import generate_debian_directory
from ppa_publish.config import (
    PPAConfig, PackageInfo, Maintainer, PPAInfo,
    Dependencies, InstallMapping
)


@pytest.fixture
def sample_config():
    return PPAConfig(
        package=PackageInfo(
            name="test-package",
            description="Test package for testing",
            section="utils",
            license="MIT",
            homepage="https://github.com/test/repo"
        ),
        maintainer=Maintainer(
            name="Test User",
            email="test@example.com"
        ),
        ppa=PPAInfo(
            username="testuser",
            ppa_name="test-ppa"
        ),
        releases=["noble", "jammy"],
        dependencies=Dependencies(
            build=["debhelper (>= 10)"],
            runtime=["bash (>= 4.0)"]
        ),
        install_files=[
            InstallMapping(source="bin/test.sh", dest="usr/bin/")
        ]
    )


def test_generate_debian_directory(tmp_path, sample_config):
    generate_debian_directory(sample_config, tmp_path)
    debian_dir = tmp_path / "debian"
    assert (debian_dir / "changelog").exists()
    assert (debian_dir / "control").exists()
    assert (debian_dir / "rules").exists()
    assert (debian_dir / "install").exists()
    assert (debian_dir / "copyright").exists()
    assert (debian_dir / "compat").exists()
    assert (debian_dir / "source" / "format").exists()


def test_debian_rules_executable(tmp_path, sample_config):
    generate_debian_directory(sample_config, tmp_path)
    rules = tmp_path / "debian" / "rules"
    import os
    assert os.access(rules, os.X_OK)


def test_debian_rules_has_tabs(tmp_path, sample_config):
    generate_debian_directory(sample_config, tmp_path)
    rules = tmp_path / "debian" / "rules"
    content = rules.read_text()
    assert '\t' in content
    assert '\n    dh' not in content


def test_no_crlf_in_generated_files(tmp_path, sample_config):
    generate_debian_directory(sample_config, tmp_path)
    debian_dir = tmp_path / "debian"
    for file in debian_dir.rglob('*'):
        if file.is_file():
            content = file.read_bytes()
            assert b'\r\n' not in content, f"{file} has CRLF line endings"
