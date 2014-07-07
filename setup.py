from setuptools import setup, find_packages

from airbrake import __version__ as version
from airbrake import __url__ as url

dependencies = [
    'requests>=2.2.1'
]
tests_require = [
    'mock',
    'testfixtures'
]

setup(
    name='airbrake',
    description='Airbrake API implementation',
    keywords='airbrake exception',
    version=version,
    author="BK Box, Sam Stavinoha",
    author_email="bk@theboxes.org",
    url=url,
    tests_require=tests_require,
    test_suite='tests',
    install_requires=dependencies,
    packages=find_packages(exclude=['tests']),
    classifiers=["Programming Language :: Python"],
    license='Apache License (2.0)'
)
