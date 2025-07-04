from setuptools import setup, find_packages

setup(
    name="system-maintenance-tools",
    version="1.0.0",
    description="Windows System Maintenance Tools",
    author="System Administrator",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
        "psutil>=5.9.0",
        "pywin32>=306",
    ],
    entry_points={
        'console_scripts': [
            'system-tools=main:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
