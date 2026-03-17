import pytest
from pathlib import Path
from ppa_publish.validators import (
    ValidationResult,
    ValidationError,
    ValidationWarning,
    check_line_endings,
    check_executable,
    check_debian_rules_tabs,
    check_email_format,
    check_debian_section,
)


def test_validation_result_no_issues():
    result = ValidationResult()
    assert not result.has_errors()
    assert not result.has_warnings()


def test_validation_result_with_error():
    result = ValidationResult()
    result.add_error("Test error")
    assert result.has_errors()
    assert len(result.errors) == 1


def test_validation_result_with_warning():
    result = ValidationResult()
    result.add_warning("Test warning")
    assert result.has_warnings()
    assert len(result.warnings) == 1


def test_check_line_endings_lf(tmp_path):
    script = tmp_path / "test.sh"
    script.write_bytes(b"#!/bin/bash\necho 'test'\n")
    result = check_line_endings(script)
    assert not result.has_errors()


def test_check_line_endings_crlf(tmp_path):
    script = tmp_path / "test.sh"
    script.write_bytes(b"#!/bin/bash\r\necho 'test'\r\n")
    result = check_line_endings(script)
    assert result.has_errors()
    assert "CRLF" in result.errors[0]


def test_check_executable_true(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text("#!/bin/bash\n")
    script.chmod(0o755)
    result = check_executable(script)
    assert not result.has_errors()


def test_check_executable_false(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text("#!/bin/bash\n")
    script.chmod(0o644)
    result = check_executable(script)
    assert result.has_errors()
    assert "not executable" in result.errors[0]


def test_check_debian_rules_tabs_valid(tmp_path):
    rules = tmp_path / "rules"
    rules.write_text("#!/usr/bin/make -f\n\n%:\n\tdh $@\n")
    result = check_debian_rules_tabs(rules)
    assert not result.has_errors()


def test_check_debian_rules_tabs_invalid(tmp_path):
    rules = tmp_path / "rules"
    rules.write_text("#!/usr/bin/make -f\n\n%:\n    dh $@\n")
    result = check_debian_rules_tabs(rules)
    assert result.has_errors()
    assert "spaces" in result.errors[0]
    assert "line 4" in result.errors[0]


def test_check_email_format_valid():
    result = check_email_format("user@example.com")
    assert not result.has_errors()


def test_check_email_format_invalid():
    result = check_email_format("not-an-email")
    assert result.has_errors()
    assert "Invalid email" in result.errors[0]


def test_check_debian_section_valid():
    result = check_debian_section("utils")
    assert not result.has_errors()


def test_check_debian_section_invalid():
    result = check_debian_section("testing")
    assert result.has_errors()
    assert "Invalid section" in result.errors[0]


from ppa_publish.validators import (
    check_install_files_exist,
    check_gpg_key_exists,
    validate_project,
)
from ppa_publish.config import PPAConfig, PackageInfo, Maintainer, PPAInfo, Dependencies, InstallMapping


def test_check_install_files_exist_all_present(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "test.sh").write_text("#!/bin/bash\n")
    install_files = [InstallMapping(source="bin/test.sh", dest="usr/bin/")]
    result = check_install_files_exist(tmp_path, install_files)
    assert not result.has_errors()


def test_check_install_files_exist_missing(tmp_path):
    install_files = [InstallMapping(source="bin/missing.sh", dest="usr/bin/")]
    result = check_install_files_exist(tmp_path, install_files)
    assert result.has_errors()
    assert "not found" in result.errors[0]


def test_validate_project_comprehensive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "bin").mkdir()
    script = tmp_path / "bin" / "test.sh"
    script.write_text("#!/bin/bash\necho 'test'\n")
    script.chmod(0o755)

    (tmp_path / "debian").mkdir()
    rules = tmp_path / "debian" / "rules"
    rules.write_text("#!/usr/bin/make -f\n\n%:\n\tdh $@\n")
    rules.chmod(0o755)

    config = PPAConfig(
        package=PackageInfo(name="test", description="Test", section="utils"),
        maintainer=Maintainer(name="Test", email="test@example.com"),
        ppa=PPAInfo(username="test", ppa_name="test"),
        releases=["noble"],
        dependencies=Dependencies(build=["debhelper (>= 10)"], runtime=[]),
        install_files=[InstallMapping(source="bin/test.sh", dest="usr/bin/")],
    )

    result = validate_project(tmp_path, config)
    assert not result.has_errors()
