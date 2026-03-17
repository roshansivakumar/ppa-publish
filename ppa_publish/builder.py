"""Build, sign, and upload workflow for PPA publishing."""

from pathlib import Path
from typing import List
import subprocess
import tempfile

from ppa_publish.config import PPAConfig
from ppa_publish.utils import format_version_for_release, format_rfc2822_date
from ppa_publish.validators import validate_project, ValidationError


class BuildError(Exception):
    """Build process failed."""
    pass


def update_changelog_for_release(
    changelog_path: Path,
    package_name: str,
    version: str,
    distribution: str,
    maintainer_name: str,
    maintainer_email: str,
    changes: List[str]
):
    """
    Update debian/changelog with new release entry.
    Prepends new entry to existing changelog.
    """
    date_str = format_rfc2822_date()
    change_lines = '\n'.join(f'  * {change}' for change in changes)

    new_entry = f"""{package_name} ({version}) {distribution}; urgency=medium

{change_lines}

 -- {maintainer_name} <{maintainer_email}>  {date_str}

"""

    if changelog_path.exists():
        existing = changelog_path.read_text()
        changelog_path.write_text(new_entry + existing)
    else:
        changelog_path.write_text(new_entry)


def build_source_package(project_root: Path) -> Path:
    """
    Build source package using dpkg-buildpackage.
    Returns path to .changes file.
    """
    cmd = ['dpkg-buildpackage', '-S', '-sa', '-us', '-uc']

    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log_path = Path(tempfile.gettempdir()) / "ppa-publish-build.log"
        log_path.write_text(result.stdout + "\n" + result.stderr)
        raise BuildError(
            f"dpkg-buildpackage failed (exit code {result.returncode})\n"
            f"View log: {log_path}"
        )

    parent = project_root.parent
    changes_files = list(parent.glob("*_source.changes"))

    if not changes_files:
        raise BuildError("No .changes file found after build")

    return changes_files[-1]


def sign_package(changes_file: Path, gpg_key_id: str):
    """Sign package with GPG using debsign."""
    cmd = ['debsign', '-k', gpg_key_id, str(changes_file)]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise BuildError(f"debsign failed: {result.stderr}")


def upload_to_ppa(
    changes_file: Path,
    ppa_username: str,
    ppa_name: str,
    force: bool = False
):
    """Upload package to PPA using dput."""
    ppa_target = f"ppa:{ppa_username}/{ppa_name}"
    cmd = ['dput']

    if force:
        cmd.append('-f')

    cmd.extend([ppa_target, str(changes_file)])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise BuildError(
            f"dput failed: {result.stderr}\n\n"
            f"Common causes:\n"
            f"  - Package already uploaded (use --force to re-upload)\n"
            f"  - GPG key not registered with Launchpad\n"
            f"  - Network issues"
        )


def release_to_ppa(
    config: PPAConfig,
    version: str,
    message: str = None,
    force: bool = False,
    only_releases: List[str] = None
):
    """
    Build and upload package to PPA for all configured releases.
    """
    project_root = Path.cwd()

    # Validate first
    validation_result = validate_project(project_root, config)

    if validation_result.has_errors():
        raise ValidationError(
            f"Validation failed with {len(validation_result.errors)} errors"
        )

    releases = only_releases or config.releases

    changelog_path = project_root / "debian" / "changelog"
    changelog_backup = changelog_path.read_text()

    try:
        changes = [message] if message else ["Release version " + version]

        for release_name in releases:
            versioned = format_version_for_release(version, release_name)

            # Update changelog
            update_changelog_for_release(
                changelog_path=changelog_path,
                package_name=config.package.name,
                version=versioned,
                distribution=release_name,
                maintainer_name=config.maintainer.name,
                maintainer_email=config.maintainer.email,
                changes=changes
            )

            # Build
            changes_file = build_source_package(project_root)

            # Sign
            if config.gpg and config.gpg.key_id:
                sign_package(changes_file, config.gpg.key_id)
            else:
                raise BuildError("No GPG key configured. Run 'ppa-publish setup-gpg'")

            # Upload
            upload_to_ppa(
                changes_file,
                config.ppa.username,
                config.ppa.ppa_name,
                force=force
            )

            # Restore changelog for next iteration
            changelog_path.write_text(changelog_backup)

    finally:
        # Always restore original changelog
        changelog_path.write_text(changelog_backup)
