from setuptools import setup, find_packages

setup(
    name="crypto-monitor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "websockets>=9.1",
        "click>=8.0.4",
        "colorama>=0.4.5",
        "python-dateutil>=2.8.2",
        "simpleaudio>=1.0.4",
        "rich>=12.6.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "crypto-monitor=monitor.cli:main",
        ],
    },
    python_requires=">=3.6.0",
) 