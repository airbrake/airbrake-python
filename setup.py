from setuptools import setup, find_packages

dependencies = [
    'requests>=2.2.1'
]

setup(
    name='airbrake',
    description='Airbrake API implementation',
    keywords='airbrake exception',
    version="1.0.0",
    author="BK Box",
    author_email="bk@theboxes.org",
    url='https://github.com/airbrake/airbrake-python',
    install_requires=dependencies,
    packages=find_packages(exclude=['tests']),
    classifiers=["Programming Language :: Python"],
    license='Apache License (2.0)'
)
