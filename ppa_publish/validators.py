"""Validation engine to catch common PPA build failures."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import os
import re

from ppa_publish.config import PPAConfig


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


def check_debian_rules_tabs(rules_path: Path) -> ValidationResult:
    """Check debian/rules uses tabs, not spaces."""
    result = ValidationResult()
    with open(rules_path) as f:
        for line_num, line in enumerate(f, 1):
            if line.startswith('    '):
                result.add_error(
                    f"debian/rules line {line_num} uses spaces, must use tabs\n"
                    f"Fix: Replace spaces with tab character"
                )
    return result


def check_email_format(email: str) -> ValidationResult:
    """Check maintainer email is properly formatted."""
    result = ValidationResult()
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        result.add_error(f"Invalid email format: {email}")
    return result


VALID_SECTIONS = {
    'admin', 'cli-mono', 'comm', 'database', 'debug', 'devel',
    'doc', 'editors', 'education', 'electronics', 'embedded',
    'fonts', 'games', 'gnome', 'gnu-r', 'gnustep', 'graphics',
    'hamradio', 'haskell', 'httpd', 'interpreters', 'introspection',
    'java', 'javascript', 'kde', 'kernel', 'libdevel', 'libs',
    'lisp', 'localization', 'mail', 'math', 'metapackages', 'misc',
    'net', 'news', 'ocaml', 'oldlibs', 'otherosfs', 'perl', 'php',
    'python', 'ruby', 'rust', 'science', 'shells', 'sound', 'tasks',
    'tex', 'text', 'utils', 'vcs', 'video', 'web', 'x11', 'xfce', 'zope'
}


def check_debian_section(section: str) -> ValidationResult:
    """Check debian section is valid per Debian Policy Manual."""
    result = ValidationResult()
    if section not in VALID_SECTIONS:
        result.add_error(
            f"Invalid section '{section}'.\n"
            f"Valid sections: {', '.join(sorted(VALID_SECTIONS)[:10])}..."
        )
    return result


def check_install_files_exist(project_root, install_files):
    """Check all install source files exist."""
    result = ValidationResult()
    for mapping in install_files:
        source_path = project_root / mapping.source
        if not source_path.exists():
            result.add_error(
                f"Install source file not found: {mapping.source}\n"
                f"Fix: Create the file or remove from install list"
            )
    return result


def check_gpg_key_exists(email):
    """Check if GPG key exists for maintainer email."""
    result = ValidationResult()
    import subprocess
    try:
        proc = subprocess.run(
            ['gpg', '--list-secret-keys', email],
            capture_output=True, text=True
        )
        if proc.returncode != 0:
            result.add_warning(
                f"No GPG key found for {email}\n"
                f"Fix: Run 'ppa-publish setup-gpg'"
            )
    except FileNotFoundError:
        result.add_warning("GPG not installed")
    return result


def validate_project(project_root, config: PPAConfig):
    """Run all validators on the project."""
    combined = ValidationResult()

    email_result = check_email_format(config.maintainer.email)
    combined.errors.extend(email_result.errors)
    combined.warnings.extend(email_result.warnings)

    section_result = check_debian_section(config.package.section)
    combined.errors.extend(section_result.errors)
    combined.warnings.extend(section_result.warnings)

    install_result = check_install_files_exist(project_root, config.install_files)
    combined.errors.extend(install_result.errors)
    combined.warnings.extend(install_result.warnings)

    for mapping in config.install_files:
        source_path = project_root / mapping.source
        if source_path.exists():
            line_result = check_line_endings(source_path)
            combined.errors.extend(line_result.errors)

            if source_path.suffix == '.sh':
                exec_result = check_executable(source_path)
                combined.errors.extend(exec_result.errors)

    rules_path = project_root / "debian" / "rules"
    if rules_path.exists():
        rules_result = check_debian_rules_tabs(rules_path)
        combined.errors.extend(rules_result.errors)

        exec_result = check_executable(rules_path)
        combined.errors.extend(exec_result.errors)

    gpg_result = check_gpg_key_exists(config.maintainer.email)
    combined.warnings.extend(gpg_result.warnings)

    return combined
