#!/usr/bin/env python3
"""
Setup script for TNS Booking Uploader Bot.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="tns-booking-uploader-bot",
    version="1.0.0",
    description="A Python desktop application for automating booking data uploads to iCabbi portal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TNS Development Team",
    author_email="dev@tns.com",
    url="https://github.com/tns/booking-uploader-bot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "build": [
            "pyinstaller>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "tns-uploader=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="automation, excel, web-scraping, gui, desktop-application",
    project_urls={
        "Bug Reports": "https://github.com/tns/booking-uploader-bot/issues",
        "Source": "https://github.com/tns/booking-uploader-bot",
    },
)
