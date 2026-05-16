from setuptools import setup, find_packages

setup(
    name="BrowserProfileManager",
    version="0.3.0",
    description="A library to scan and launch browser profiles using CDP for Playwright.",
    packages=find_packages(),
    install_requires=[
        "playwright"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
    ],
)
