from setuptools import setup, find_packages

setup(
    name="ProcessSentinel",
    version="1.1.0",
    author="Jules",
    description="A utility to monitor and manage Python and Node.js processes.",
    packages=find_packages(),
    entry_points={
        'gui_scripts': [
            'sentinel = python_memory_sentinel.main:main',
        ],
    },
    install_requires=[
        "psutil",
        "PyQt6",
        "pyqtgraph",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
