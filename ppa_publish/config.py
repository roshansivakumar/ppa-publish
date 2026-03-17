"""Configuration management for ppa-publish."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import yaml


class ConfigError(Exception):
    """Configuration file is invalid or missing."""
    pass


@dataclass
class PackageInfo:
    """Package metadata."""
    name: str
    description: str
    section: str = "utils"
    license: str = "MIT"
    homepage: str = ""


@dataclass
class Maintainer:
    """Package maintainer information."""
    name: str
    email: str


@dataclass
class PPAInfo:
    """Launchpad PPA information."""
    username: str
    ppa_name: str


@dataclass
class Dependencies:
    """Build and runtime dependencies."""
    build: List[str]
    runtime: List[str]


@dataclass
class InstallMapping:
    """Mapping of source files to destination paths."""
    source: str
    dest: str


@dataclass
class Scripts:
    """Optional debian maintainer scripts."""
    postinst: Optional[str] = None
    postrm: Optional[str] = None
    config: Optional[str] = None
    templates: Optional[str] = None


@dataclass
class GPGInfo:
    """GPG key information."""
    key_id: Optional[str] = None


@dataclass
class PPAConfig:
    """Complete PPA publishing configuration."""
    package: PackageInfo
    maintainer: Maintainer
    ppa: PPAInfo
    releases: List[str]
    dependencies: Dependencies
    install_files: List[InstallMapping]
    scripts: Optional[Scripts] = None
    gpg: Optional[GPGInfo] = None


def load_config(config_path: Path) -> PPAConfig:
    """
    Load and validate .ppa-publish.yml configuration.

    Args:
        config_path: Path to .ppa-publish.yml

    Returns:
        PPAConfig instance

    Raises:
        ConfigError: If config is missing, invalid, or incomplete
    """
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Config must be a YAML object, got {type(data)}")

    try:
        package_data = data.get("package", {})
        package = PackageInfo(
            name=package_data["name"],
            description=package_data["description"],
            section=package_data.get("section", "utils"),
            license=package_data.get("license", "MIT"),
            homepage=package_data.get("homepage", ""),
        )

        maint_data = data.get("maintainer", {})
        maintainer = Maintainer(
            name=maint_data["name"],
            email=maint_data["email"],
        )

        ppa_data = data.get("ppa", {})
        ppa = PPAInfo(
            username=ppa_data["username"],
            ppa_name=ppa_data["ppa_name"],
        )

        releases = data.get("releases", [])
        if not releases:
            raise ConfigError("At least one Ubuntu release is required")

        deps_data = data.get("dependencies", {})
        dependencies = Dependencies(
            build=deps_data.get("build", []),
            runtime=deps_data.get("runtime", []),
        )

        install_data = data.get("install", [])
        install_files = [
            InstallMapping(source=item["source"], dest=item["dest"])
            for item in install_data
        ]

        scripts_data = data.get("scripts")
        scripts = None
        if scripts_data:
            scripts = Scripts(
                postinst=scripts_data.get("postinst"),
                postrm=scripts_data.get("postrm"),
                config=scripts_data.get("config"),
                templates=scripts_data.get("templates"),
            )

        gpg_data = data.get("gpg")
        gpg = None
        if gpg_data:
            gpg = GPGInfo(key_id=gpg_data.get("key_id"))

        return PPAConfig(
            package=package,
            maintainer=maintainer,
            ppa=ppa,
            releases=releases,
            dependencies=dependencies,
            install_files=install_files,
            scripts=scripts,
            gpg=gpg,
        )

    except KeyError as e:
        raise ConfigError(f"Missing required field in config: {e}")
    except (TypeError, ValueError) as e:
        raise ConfigError(f"Invalid config format: {e}")
