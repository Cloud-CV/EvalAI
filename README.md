# EvalAI-CLI

Official Command Line utility to use EvalAI in your terminal.

------------------------------------------------------------------------------------------

[![Join the chat at https://gitter.im/Cloud-CV/EvalAI](https://badges.gitter.im/Cloud-CV/EvalAI.svg)](https://gitter.im/Cloud-CV/EvalAI?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/Cloud-CV/evalai-cli.svg?branch=master)](https://travis-ci.org/Cloud-CV/evalai-cli)
[![Coverage Status](https://coveralls.io/repos/github/Cloud-CV/evalai-cli/badge.svg?branch=master)](https://coveralls.io/github/Cloud-CV/evalai-cli?branch=master)

## Goal

The goal of this package is to offer almost all the features available on the website within your terminal.

## Development Setup

### Step 1:

Setup the development environment for EvalAI and make sure that django server & submission worker is running perfectly

### Step 2:

1. Clone the evalai-cli repository to your machine via git

```bash
git clone https://github.com/Cloud-CV/evalai-cli.git EvalAI-CLI
```

2. Create a virtual environment

```bash
$ cd EvalAI-CLI
$ virtualenv -v python3 venv
$ source venv/bin/activate
```
3. Install the package dependencies

```bash
$ pip install -r requirements.txt
```

4. Install the package locally to try it out

```bash
$ pip install -e .
```

## Contributing Guidelines

If you are interested in contributing to EvalAI-CLI, follow our [contribution guidelines](https://github.com/Cloud-CV/evalai-cli/blob/master/.github/CONTRIBUTING.md).
