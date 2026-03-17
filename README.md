# ppa-publish

Automate the painful parts of publishing packages to Ubuntu PPAs.

## Installation

```bash
pip install ppa-publish
```

## Quick Start

```bash
# Initialize project
ppa-publish init

# Setup GPG (one-time)
ppa-publish setup-gpg

# Validate before building
ppa-publish validate

# Release to PPA
ppa-publish release 1.0.0
```

## Features

- Generates debian/ directory from simple config
- 19 validators catch common build failures
- Supports multiple Ubuntu releases (noble, jammy, focal)
- Clear error messages with fix commands
- Reduces publish time from 4 hours to 30 minutes

## Documentation

See [docs/](docs/) for detailed guides.

## License

MIT
