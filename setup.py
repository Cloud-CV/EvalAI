#!/usr/bin/env python
from setuptools import setup, find_packages


PROJECT = 'evalai'


long_description = \
    'https://github.com/Cloud-CV/evalai_cli/blob/master/README.md'

setup(
    name=PROJECT,
    version='1.6a1',

    description='Use EvalAI through the CLI!',
    long_description=long_description,

    author='Cloud-CV',
    author_email='team@cloudcv.org',

    url='https://github.com/Cloud-CV/evalai_cli ',

    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=[
        'beautifulsoup4==4.6.0',
        'beautifultable==0.5.0',
        'click==6.7',
        'lxml==4.2.1',
        'python-dateutil==2.7.3',
        'requests==2.18.4',
        'responses==0.9.0',
    ],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'evalai=evalai.main:main',
        ],
    },

    zip_safe=False,
)
