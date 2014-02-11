import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

DEPENDENCYLINKS = []
REQUIRES = []


setup(
    name='airbrake',
    description='Airbrake API implementation',
    keywords='airbrake exception',
    version="1.0.0",
    author="BK Box",
    author_email="bk@theboxes.org",
    dependency_links=DEPENDENCYLINKS,
    install_requires=REQUIRES,
    packages=find_packages(exclude=['bin', 'ez_setup']),
    namespace_packages=['airbrake'],
    license='Apache License (2.0)',
)
