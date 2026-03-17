"""Generate debian/ directory from templates."""

from pathlib import Path
from datetime import datetime
import jinja2
from ppa_publish.config import PPAConfig
from ppa_publish.utils import format_rfc2822_date


def generate_debian_directory(config: PPAConfig, project_root: Path):
    """
    Generate complete debian/ directory from templates.
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('ppa_publish', 'templates'),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    debian_dir = project_root / 'debian'
    debian_dir.mkdir(exist_ok=True)

    source_dir = debian_dir / 'source'
    source_dir.mkdir(exist_ok=True)

    context = {
        'package_name': config.package.name,
        'version': '0.1.0',
        'distribution': 'UNRELEASED',
        'changes': ['Initial package'],
        'maintainer_name': config.maintainer.name,
        'maintainer_email': config.maintainer.email,
        'date_rfc2822': format_rfc2822_date(),
        'section': config.package.section,
        'build_deps': config.dependencies.build,
        'runtime_deps': config.dependencies.runtime,
        'short_description': config.package.description.split('\n')[0][:79],
        'long_description_lines': config.package.description.split('\n')[1:] if '\n' in config.package.description else [],
        'homepage': config.package.homepage,
        'install_files': config.install_files,
        'license': config.package.license,
        'year': datetime.now().year,
    }

    templates = [
        ('changelog.j2', debian_dir / 'changelog'),
        ('control.j2', debian_dir / 'control'),
        ('rules.j2', debian_dir / 'rules'),
        ('install.j2', debian_dir / 'install'),
        ('copyright.j2', debian_dir / 'copyright'),
        ('compat.j2', debian_dir / 'compat'),
        ('source_format.j2', source_dir / 'format'),
    ]

    for template_name, output_path in templates:
        template = env.get_template(template_name)
        content = template.render(**context)
        # Force LF line endings
        output_path.write_text(content, newline='\n')
        # Make rules executable
        if output_path.name == 'rules':
            output_path.chmod(0o755)
