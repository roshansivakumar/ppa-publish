import pytest
from pathlib import Path
from ppa_publish.builder import update_changelog_for_release


def test_update_changelog_for_release(tmp_path):
    """Test updating changelog for specific release"""
    debian_dir = tmp_path / "debian"
    debian_dir.mkdir()

    changelog = debian_dir / "changelog"
    changelog.write_text("""test-package (0.1.0) UNRELEASED; urgency=medium

  * Initial package

 -- Test User <test@example.com>  Mon, 01 Jan 2024 12:00:00 +0000
""")

    update_changelog_for_release(
        changelog_path=changelog,
        package_name="test-package",
        version="1.0.0",
        distribution="noble",
        maintainer_name="Test User",
        maintainer_email="test@example.com",
        changes=["First release"]
    )

    content = changelog.read_text()
    assert "test-package (1.0.0) noble" in content
    assert "First release" in content
