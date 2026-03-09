## Contributing guidelines

Thank you for your interest in contributing to EvalAI! Here are some contribution guidelines to help you get started.

### Setting things up

To set up the development environment, follow the instructions in README.

### Getting started as a contributor

The EvalAI issue tracker is the primary place to start contributing. If an issue aligns with your interests,leave a comment on the thread and the maintainers will guide you through the next steps.

The existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., that can help you in selecting one.

Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. 

If neither of these seem appealing, please post on our channel and we will help find you something else to work on.

### Instructions to submit code

Before you submit code, please talk to us via the issue tracker so we know you are working on it.

Our main/central development branch is `master`. New work should be done on feature branches created from `master` and merged back once the changes are stable and reviewed. To submit code, follow these steps:

1. Create a new branch off of `master`. Select a descriptive branch name.

        git remote add upstream git@github.com:Cloud-CV/EvalAI.git
        git fetch upstream
        git checkout master
        git merge upstream/master
        git checkout -b your-branch-name

    We strongly encourage using [black](http://www.github.com/psf/black)
    to format your code. Black follows PEP8 conventions and ensures consistency across the codebase.
    This repository is already configured with [pre-commit hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
    to automatically run black and flake8 before each commit. To activate the hooks, you just need to run
    the following comamnd once:

        pre-commit install

2. Commit and push code to your branch:

    - Commits should be self-contained and include a descriptive commit message.
        ##### Guidelines for writing effective Git commit messages
        - Separate subject from body with a blank line
        - Do not end the subject line with a period
        - Capitalize the subject line and each paragraph
        - Use the imperative mood in the subject line
        - Wrap lines at 72 characters
        - Use the body to explain what and why you have done something. In most cases, you can leave out details about how a change has been made.

        ##### Example for a commit message
            Subject of the commit message

            Body of the commit message...
            ....

    - Please make sure your code is well-formatted and adheres to PEP8 conventions (for Python) and the airbnb style guide (for JavaScript). For others (Lua, prototxt etc.) please ensure that the code is well-formatted and the style consistent.
    - Please ensure that your code is well tested.
    - We highly encourage to use `autopep8` to follow the PEP8 styling. Run the following command before creating the pull request:

            autopep8 --in-place --exclude env,docs --recursive .     
            git commit -a -m “{{commit_message}}”
            git push origin {{branch_name}}

    - Additionally, use an HTML/CSS/JS formatter to keep frontend code clean and consistent.
    - To install the Sublime Text Package Control Manager use [this](https://packagecontrol.io/installation#st2) link. 
      If Sublime Package Control Manager is already installed, use it to install an HTML/CSS/JS code formatter.

3. Once the code is pushed, create a pull request:

    - On your GitHub fork, select your branch and click “New pull request”. choose `master` as the base branch and your branch as the `compare` branch.
If Github indicates that the branch can be merged (for example, showing "Able to merge"), proceed to create the pull request.
    - After submitting the pull request, check back to ensure that the Travis CI checks have passed. If the build fails, click the "Details" link next to the failed check on your PR to view the build logs. Review the errors shown there and resolve the issues before updating your pull request.

    - If your checks have passed, your PR will be assigned a reviewer who will review your code and provide comments. Please address each review comment by pushing new commits to the same branch (the PR will automatically update, so you don’t need to submit a new one). Once you are done, comment below each review comment marking it as “Done”. Feel free to use the thread to have a discussion about comments that you don’t understand completely or don’t agree with.

    - Once all comments are addressed, the maintainer will approve the PR.

4. Once your code has been reviewed by a maintainer and all required changes are completed, squash all commits.
   The commands below can be used to squash your commits:

            git checkout <branch_name>
            git rebase -i HEAD~N (N is the number of commits to be squashed)
    - Then a screen will appear with all N commits having `pick` written in front of every commit.Change `pick` to `s` (squash) for the last N-1 commits and let it be pick for the first one.
    - Press esc button and type ":wq" to save the change and close the screen. Now a new screen will appear asking you to change commit message. Change it accordingly and save it.
            git push origin <branch_name> --force

    - For further query regarding rebasing, visit https://github.com/todotxt/todo.txt-android/wiki/Squash-All-Commits-Related-to-a-Single-Issue-into-a-Single-Commit
    - Once rebasing is done, the reviewer will approve and merge the PR.

Congratulations, you have successfully contributed to Project EvalAI!
