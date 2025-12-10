from setuptools import setup, find_packages

setup(
    name="infrastructure-lib",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "cdktf>=0.20.0",
        "cdktf-cdktf-provider-google>=13.0.0",
        "constructs>=10.0.0"
    ],
    description="Generic Infrastructure Library for Cross Platform",
    author="Platform Team",
)
