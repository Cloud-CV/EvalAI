#!/usr/bin/env python
import io

from setuptools import setup, find_packages


PROJECT = 'evalai'


with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=PROJECT,
    version='1.0.17',

    description='Use EvalAI through the CLI!',
    long_description=long_description,
    long_description_content_type='text/markdown',

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
        'requests==2.20.0',
        'responses==0.9.0',
        'validators==0.12.2',
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
