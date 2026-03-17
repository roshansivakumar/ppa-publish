from ppa_publish.utils import format_version_for_release, format_rfc2822_date
import re


def test_format_version_noble():
    """Noble (latest) gets no suffix"""
    assert format_version_for_release("1.0.0", "noble") == "1.0.0"


def test_format_version_jammy():
    """Jammy gets ~jammy1 suffix"""
    assert format_version_for_release("1.0.0", "jammy") == "1.0.0~jammy1"


def test_format_version_focal():
    """Focal gets ~focal1 suffix"""
    assert format_version_for_release("1.0.0", "focal") == "1.0.0~focal1"


def test_format_version_incremental():
    """Test incremental backport versions"""
    assert format_version_for_release("1.0.0", "jammy", increment=2) == "1.0.0~jammy2"
    assert format_version_for_release("1.0.0", "focal", increment=3) == "1.0.0~focal3"


def test_rfc2822_date_format():
    """Test RFC 2822 date formatting"""
    date_str = format_rfc2822_date()
    pattern = r"^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{4}$"
    assert re.match(pattern, date_str), f"Invalid date format: {date_str}"
