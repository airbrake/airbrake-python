"""Airbrake-Python packaging and installation."""

import os
import subprocess
import sys

from setuptools import find_packages
from setuptools import setup


src_dir = os.path.dirname(os.path.realpath(__file__))
about = {}
with open(os.path.join(src_dir, 'airbrake', '__about__.py')) as abt:
    exec(abt.read(), about)  # pylint: disable=exec-used


# README.rst is for PyPI page
# pandoc --from=markdown_github --to=rst README.md --output=README.rst
LONG_DESCRIPTION = ''
readme_rst = os.path.join(src_dir, 'README.rst')
if os.path.isfile(readme_rst):
    with open(readme_rst) as rdme:
        LONG_DESCRIPTION = rdme.read()


# Add the commit hash to the keywords for sanity.
if any(k in ' '.join(sys.argv).lower() for k in ['upload', 'dist']):
    try:
        current_commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD']).strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    else:
        if current_commit and len(current_commit) == 40:
            about['__keywords__'].append(current_commit[:8])


CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Topic :: Software Development',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
]


INSTALL_REQUIRES = [
    'requests>=2.8.1'
]


TESTS_REQUIRE = [
    'coverage>=4.0',
    'flake8>=2.4.1',
    'flake8-docstrings>=0.2.1.post1',
    'mock>=1.3.0',
    'nose>=1.3.7',
    'pylint>=1.4.4',
    'testfixtures>=4.3.3',
]


package_attributes = {
    'author': about['__author__'],
    'author_email': about['__email__'],
    'classifiers': CLASSIFIERS,
    'description': about['__summary__'],
    'install_requires': INSTALL_REQUIRES,
    'keywords': ' '.join(about['__keywords__']),
    'license': about['__license__'],
    'long_description': LONG_DESCRIPTION,
    'name': about['__title__'],
    'packages': find_packages(exclude=['tests']),
    'test_suite': 'tests',
    'url': about['__url__'],
    'version': about['__version__'],
}

setup(**package_attributes)
