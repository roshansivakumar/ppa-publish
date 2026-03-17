from setuptools import setup, find_packages

setup(
    name="ppa-publish",
    version="0.1.0",
    description="Automate Ubuntu PPA publishing for CLI tools",
    author="Roshan Sivakumar",
    author_email="roshan.sivakumar001@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "jinja2>=3.0.0",
        "pyyaml>=6.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ppa-publish=ppa_publish.cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
