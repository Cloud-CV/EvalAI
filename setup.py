#!/usr/bin/env python
from setuptools import setup, find_packages


PROJECT = 'evalai'


long_description = \
    'https://github.com/Cloud-CV/evalai_cli/blob/master/README.md'

setup(
    name=PROJECT,
    version='1.0',

    description='Use EvalAI through the CLI!',

    author='Cloud-CV',
    author_email='team@cloudcv.org',

    url='https://github.com/Cloud-CV/evalai_cli',
    download_url='https://github.com/Cloud-CV/evalai_cli/tarball/master',

    classifiers=['Development Status :: 1 - Alpha',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=[
        'click==6.7',
        'pandas==0.22.0',
        'pylsy==3.6',
        'requests==2.18.4',
        'responses==0.9.0',
    ],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points=
        '''
        [console_scripts]
        evalai = evalai.main:main
        ''',

    zip_safe=False,
)
