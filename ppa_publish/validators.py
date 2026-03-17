"""Validation engine to catch common PPA build failures."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import os


@dataclass
class ValidationResult:
    """Result of running validators."""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ValidationError(Exception):
    """Validation failed with errors."""
    pass


class ValidationWarning(Exception):
    """Validation completed with warnings."""
    pass


def check_line_endings(file_path: Path) -> ValidationResult:
    """
    Check if file has CRLF (Windows) line endings.
    Why: Causes "/usr/bin/env: 'bash\\r': No such file or directory"
    """
    result = ValidationResult()
    with open(file_path, 'rb') as f:
        content = f.read()
    if b'\r\n' in content:
        result.add_error(
            f"{file_path} has CRLF line endings\n"
            f"Fix: sed -i 's/\\r$//' {file_path}"
        )
    return result


def check_executable(file_path: Path) -> ValidationResult:
    """
    Check if file is executable.
    Why: Non-executable scripts fail during package install
    """
    result = ValidationResult()
    if not os.access(file_path, os.X_OK):
        result.add_error(
            f"{file_path} is not executable\n"
            f"Fix: chmod +x {file_path}"
        )
    return result
