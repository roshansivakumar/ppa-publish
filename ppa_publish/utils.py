"""Utility functions for ppa-publish."""

from email.utils import formatdate


def format_version_for_release(
    base_version: str,
    distribution: str,
    increment: int = 1
) -> str:
    """
    Format version number for specific Ubuntu release.

    Noble (latest) gets no suffix.
    Older releases get ~<codename><increment> suffix.

    Args:
        base_version: Base version like "1.0.0"
        distribution: Ubuntu codename (noble, jammy, focal, etc.)
        increment: Backport increment (default 1)

    Returns:
        Formatted version string
    """
    if distribution == "noble":
        return base_version
    return f"{base_version}~{distribution}{increment}"


def format_rfc2822_date() -> str:
    """
    Format current time as RFC 2822 date string.
    Required for debian/changelog entries.

    Returns:
        Date string like "Mon, 17 Mar 2026 14:30:00 -0400"
    """
    return formatdate(localtime=True)
