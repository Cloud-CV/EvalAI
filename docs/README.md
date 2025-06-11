## Instructions to Build & Run Documentation Locally
This guide provides instructions for setting up your environment, building, and running the EvalAI documentation on your local machine.

Building and running the documentation locally will help you to ensure accuracy, correct formatting, and preview changes before submitting a pull request.

### Prerequisites & Setup

1. Set up the Project locally

    Before building the `docs/` project, make sure you have cloned and set up EvalAI project locally.

    To set up the development environment first, follow the [installation instructions](https://github.com/Cloud-CV/EvalAI/blob/master/README.md#installation-instructions) in README.

2. Create a Virtual Environment (Recommended)

    EvalAI and its documentation tools require Python 3. We recommend using Python 3.10 or newer.
    Also, it's a best practice to work within a Python virtual environment to avoid conflicts with your system's Python packages.

    From the root directory of EvalAI project (where `requirements/` folder is located), create and activate a virtual environment:


    ```
    # Create a virtual environment with python 3.10
    python3.10 -m venv docs-env

    # Activate the virtual environment
    # On macOS/Linux:
    source docs-env/bin/activate

    # On Windows (Command Prompt):
    docs-env\Scripts\activate.bat
    ```

### Install Documentation Dependencies

With your virtual environment activated, install the specific Python packages required to build the documentation. These are listed in `requirements/readthedocs.txt`.

From the root directory of EvalAI, run the installation command:

```
pip install -r requirements/readthedocs.txt
```

### Build the Documentation
Once the dependencies are installed, build the HTML documentation.

Navigate to the docs directory and run the build command:

```
cd docs
make html
```

### View Documentation Locally
After a successful build, you can open the generated HTML files in your web browser.

From the `docs` directory, run the following command:
```
# On macOS:
open build/html/index.html

# On Windows (Command Prompt):
start build\html\index.html

# On Linux (using xdg-open for default browser):
xdg-open build/html/index.html
```

Alternatively, you can always navigate manually:

Just go to `evalai/docs/build/html/` on your file explorer/finder
and double-click `index.html`.

### Live Preview (Recommended)
For a more efficient development workflow, `sphinx-autobuild` automatically rebuilds the documentation and refreshes your web browser whenever you save changes to your documentation source files. This eliminates the need to manually run `make html` and refresh your browser repeatedly.

To start the live preview server, run the following command from the root of the project:

> Note: It's important to run this command from the root directory, NOT inside the `docs` directory.

```
sphinx-autobuild docs/source docs/build/html
```
It will start a local web server, typically at `http://127.0.0.1:8000/`. To stop the live preview server, press `Ctrl+C` in your terminal.

With this, you're ready to start contributing to the docs!

## Troubleshooting
Encountering issues? Don't worry, here are some common problems and their fixes:

- ### Incompatible Python Version: 
    Many package version errors occur mostly due to a wrong or incompatible python version.

    Hence, make sure you're using a dedicated virtual environment with `python >=3.10` (preferable) as mentioned in earlier steps, while contributing to the project.

- ### Sphnix Version Error:

    ```
    Sphinx version error:
    The sphinxcontrib.applehelp extension used by this project needs at least Sphinx vX.0; it therefore cannot be built with this version.
    make: *** [html] Error 2
    ```

    This usually occurs when you're using the wrong or outdated version of Sphinx. 
    
    Make sure you've installed docs dependencies as mentioned in the `requirements/readthedocs.txt`. (See installation steps above).

    If the issue still persists, simply run this command:

    ```
    pip install --upgrade sphinx
    ```
- ### Document not included in toctree:

    Sometimes, you'll see a warning message like this while building the docs:

    ```
    WARNING: document isn't included in any toctree: <filename.md>
    ```

    This error usually occurs when Sphinx has found a documentation source file (like a .rst or .md file) that exists, but it hasn't been explicitly listed in any `toctree` directive (e.g., `index.rst`).

    It can happen when you've likely created a new `.rst` or `.md` file, but forgot to add its entry to `index.rst` toctree.
    To fix this, mention the filename in `index.rst` file at a appropriate place and build again.

- ### Document not displayed in Live Preview:

    Newly created sections within docs might not show in the build view.

    This problem occurs due to the previous mentioned problem of `"Document not included in toctree"` and can be fixed with the same given solution.
