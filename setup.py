from setuptools import setup, find_packages

setup(
    name="invisible-terminal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyGObject>=3.46",
        "anthropic>=0.40",
        "requests>=2.31",
    ],
    entry_points={
        "console_scripts": [
            "exitt=invisible_terminal.app:main",
        ],
    },
    python_requires=">=3.11",
)
