#!/usr/bin/env python3
"""
Setup script for OWON PSU Control Library
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "OWON PSU Control Library"

# Read version from the package
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'owon_psu', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip("'\"")
    return '1.0.0'

setup(
    name='owon-psu-control',
    version=get_version(),
    author='Robbe Derks',
    author_email='robbe.derks@gmail.com',
    description='A comprehensive Python library for controlling OWON Power Supply Units via SCPI commands',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/your-repo/owon-psu-control',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.7',
    install_requires=[
        'pyserial>=3.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.800',
        ],
        'docs': [
            'sphinx>=4.0',
            'sphinx-rtd-theme>=1.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'owon-psu=owon_psu.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords='owon psu power supply scpi serial network control',
    project_urls={
        'Bug Reports': 'https://github.com/your-repo/owon-psu-control/issues',
        'Source': 'https://github.com/your-repo/owon-psu-control',
        'Documentation': 'https://github.com/your-repo/owon-psu-control#readme',
    },
)
