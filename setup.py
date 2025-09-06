"""
Setup script for Vinted Monitor.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="vinted-monitor",
    version="1.0.0",
    author="Vinted Monitor",
    author_email="",
    description="Monitor Vinted listings in near real-time with Discord notifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/vinted-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vinted-monitor=app.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["*.yaml", "*.yml"],
        "config": ["*.yaml", "*.yml"],
    },
    zip_safe=False,
    keywords="vinted, monitoring, discord, notifications, scraping, e-commerce",
    project_urls={
        "Bug Reports": "https://github.com/your-username/vinted-monitor/issues",
        "Source": "https://github.com/your-username/vinted-monitor",
        "Documentation": "https://github.com/your-username/vinted-monitor#readme",
    },
)
