from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cyberscape",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A terminal-based horror RPG with AI-driven narrative",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cyberscape",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pygame>=2.5.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
        "colorama>=0.4.6",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cyberscape=core.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cyberscape": [
            "assets/*",
            "sounds/*",
            "data/**/*",
        ],
    },
) 