"""CLI commands for ppa-publish."""

import click
from pathlib import Path
import yaml

from ppa_publish.config import load_config, ConfigError
from ppa_publish.generators.debian import generate_debian_directory
from ppa_publish.validators import validate_project
from ppa_publish.builder import release_to_ppa, BuildError
from ppa_publish.validators import ValidationError
from ppa_publish.config import (
    PPAConfig, PackageInfo, Maintainer, PPAInfo,
    Dependencies, InstallMapping
)


@click.group()
@click.version_option()
def cli():
    """PPA Publish - Automate Ubuntu PPA publishing."""
    pass


@cli.command()
def init():
    """
    Initialize PPA publishing for this project.

    Interactive wizard creates .ppa-publish.yml and debian/ directory.
    """
    config_path = Path.cwd() / ".ppa-publish.yml"

    if config_path.exists():
        click.echo("Error: .ppa-publish.yml already exists")
        click.echo("\nTo reconfigure, delete it first:")
        click.echo(f"  rm {config_path}")
        raise SystemExit(1)

    click.echo("PPA Publish - Project Initialization\n")

    project_name = Path.cwd().name
    package_name = click.prompt("Package name", default=project_name)

    short_desc = click.prompt("Short description (< 80 chars)")

    license_name = click.prompt(
        "License",
        default="MIT",
    )

    homepage = click.prompt("Homepage/repo URL", default="")

    maintainer_name = click.prompt("Maintainer name")
    maintainer_email = click.prompt("Maintainer email")

    ppa_username = click.prompt("Launchpad username")
    ppa_name = click.prompt("PPA name", default=package_name)

    releases_str = click.prompt(
        "Ubuntu releases (comma-separated)",
        default="noble,jammy"
    )
    releases = [r.strip() for r in releases_str.split(',')]

    # Detect bash scripts
    click.echo("\nDetecting bash scripts...")
    bash_scripts = list(Path.cwd().rglob("*.sh"))

    skip_extensions = {'.pyc', '.so', '.o', '.a', '.dylib', '.dll'}
    for file in Path.cwd().rglob("*"):
        if not file.is_file() or file.suffix in skip_extensions:
            continue
        try:
            content = file.read_text(errors='strict')
            if content.startswith("#!/bin/bash") and file not in bash_scripts:
                bash_scripts.append(file)
        except (UnicodeDecodeError, PermissionError):
            continue

    install_files = []
    if bash_scripts:
        click.echo(f"Found {len(bash_scripts)} bash scripts")
        for script in bash_scripts[:5]:
            if click.confirm(f"Install {script}?", default=True):
                install_files.append({
                    "source": str(script.relative_to(Path.cwd())),
                    "dest": "usr/bin/"
                })

    config_data = {
        "package": {
            "name": package_name,
            "description": short_desc,
            "section": "utils",
            "license": license_name,
            "homepage": homepage,
        },
        "maintainer": {
            "name": maintainer_name,
            "email": maintainer_email,
        },
        "ppa": {
            "username": ppa_username,
            "ppa_name": ppa_name,
        },
        "releases": releases,
        "dependencies": {
            "build": ["debhelper (>= 10)"],
            "runtime": ["bash (>= 4.0)"],
        },
        "install": install_files,
        "gpg": {
            "key_id": None,
        },
    }

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    click.echo(f"\nCreated {config_path}")

    try:
        config = load_config(config_path)
        generate_debian_directory(config, Path.cwd())
        click.echo("Generated debian/ directory")
    except Exception as e:
        click.echo(f"Error generating debian/: {e}")
        raise SystemExit(1)

    click.echo("\nNext steps:")
    click.echo("  1. Review .ppa-publish.yml (edit if needed)")
    click.echo("  2. Run: ppa-publish setup-gpg")
    click.echo("  3. Run: ppa-publish validate")
    click.echo("  4. Run: ppa-publish release 1.0.0")


@cli.command()
def validate():
    """
    Validate project before building.

    Runs all validators and reports errors/warnings.
    """
    config_path = Path.cwd() / ".ppa-publish.yml"

    if not config_path.exists():
        click.echo("Error: .ppa-publish.yml not found")
        click.echo("\nRun 'ppa-publish init' first")
        raise SystemExit(1)

    try:
        config = load_config(config_path)
    except ConfigError as e:
        click.echo(f"Config error: {e}")
        raise SystemExit(1)

    click.echo("Validating project...\n")

    result = validate_project(Path.cwd(), config)

    if result.has_errors():
        click.echo(f"{len(result.errors)} error(s) found:\n")
        for error in result.errors:
            click.echo(f"  * {error}\n")

    if result.has_warnings():
        click.echo(f"{len(result.warnings)} warning(s):\n")
        for warning in result.warnings:
            click.echo(f"  * {warning}\n")

    if not result.has_errors() and not result.has_warnings():
        click.echo("All validations passed!")
    elif result.has_errors():
        click.echo("Cannot proceed with build until errors are fixed.")
        raise SystemExit(1)
    else:
        click.echo("Validation passed with warnings.")


@cli.command()
@click.argument('version')
@click.option('--message', '-m', help='Release message')
@click.option('--force', '-f', is_flag=True, help='Force re-upload')
@click.option('--only', help='Only build for specific releases (comma-separated)')
def release(version, message, force, only):
    """
    Build and upload to PPA for all configured releases.

    VERSION: Version number (e.g., 1.0.0)

    Examples:
      ppa-publish release 1.0.0
      ppa-publish release 1.0.1 -m "Bug fix release"
      ppa-publish release 1.0.0 --only noble,jammy
    """
    config_path = Path.cwd() / ".ppa-publish.yml"

    if not config_path.exists():
        click.echo("Error: .ppa-publish.yml not found")
        raise SystemExit(1)

    try:
        config = load_config(config_path)
    except ConfigError as e:
        click.echo(f"Config error: {e}")
        raise SystemExit(1)

    only_releases = None
    if only:
        only_releases = [r.strip() for r in only.split(',')]

    try:
        release_to_ppa(
            config=config,
            version=version,
            message=message,
            force=force,
            only_releases=only_releases
        )
    except ValidationError as e:
        click.echo(f"Validation failed: {e}")
        click.echo("\nRun 'ppa-publish validate' to see details")
        raise SystemExit(1)
    except BuildError as e:
        click.echo(f"Build failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}")
        raise SystemExit(1)


if __name__ == '__main__':
    cli()
