from setuptools import setup, find_packages

setup(
    name     = 'smpipi',
    version  = '0.1',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Simple, flexible and non-restrictive SMPP client',
    long_description = open('README.rst').read(),
    packages = find_packages(exclude=['tests']),
    include_package_data = True,
    url = 'https://github.com/baverman/smpipi',
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
    ],
)
