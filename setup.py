import re
import ast
from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')
_url_re = re.compile(r'__url__\s+=\s+(.*)')


with open('airbrake/__init__.py', 'rb') as f:
    f = f.read()
    version = str(ast.literal_eval(_version_re.search(
        f.decode('utf-8')).group(1)))
    url = str(ast.literal_eval(_url_re.search(
        f.decode('utf-8')).group(1)))


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
