#!/usr/bin/env python
import io

from setuptools import setup, find_packages


PROJECT = "evalai"


with io.open("README.md", encoding="utf-8") as f:
    long_description = f.read()

install_requires = [
    'beautifulsoup4==4.7.1',
    'beautifultable==0.7.0',
    'boto==2.49.0',
    'boto3==1.9.88',
    'botocore==1.12.116',
    'click==6.7',
    'coverage==4.5.1',
    'coveralls==1.3.0',
    'docker==3.6.0',
    'flake8==3.0.4',
    'lxml==4.2.1',
    'pytest==3.5.1',
    'pytest-cov==2.5.1',
    'python-dateutil==2.7.3',
    'requests==2.20.0',
    'requests-toolbelt==0.8.0',
    'responses==0.9.0',
    'validators==0.12.2',
]

setup(
    name=PROJECT,
    version="1.1.4",
    description="Use EvalAI through command line interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cloud-CV",
    author_email="team@cloudcv.org",
    url="https://github.com/Cloud-CV/evalai_cli ",
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    platforms=["Any"],
    scripts=[],
    provides=[],
    install_requires=install_requires,
    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,
    entry_points={"console_scripts": ["evalai=evalai.main:main"]},
    zip_safe=False,
)
