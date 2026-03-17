import pytest
from pathlib import Path
from ppa_publish.validators import (
    ValidationResult,
    ValidationError,
    ValidationWarning,
    check_line_endings,
    check_executable,
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
