"""CLI commands for ppa-publish."""

import click
from pathlib import Path
import yaml

from ppa_publish.config import load_config, ConfigError
from ppa_publish.generators.debian import generate_debian_directory
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


if __name__ == '__main__':
    cli()
