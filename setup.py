#!/usr/bin/env python3
"""
Setup script for the PHP-to-Laravel Migration Analysis System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')

setup(
    name="php-laravel-migration-analyzer",
    version="1.0.0",
    description="Multi-agent system for analyzing PHP to Laravel migration projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Migration Analysis System",
    author_email="dev@example.com",
    url="https://github.com/yourorg/php-laravel-migration-analyzer",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'migration-analyzer=main:cli',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    keywords="php laravel migration analysis code-analysis static-analysis",
    project_urls={
        "Bug Reports": "https://github.com/yourorg/php-laravel-migration-analyzer/issues",
        "Source": "https://github.com/yourorg/php-laravel-migration-analyzer",
    },
)