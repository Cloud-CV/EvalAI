## Contributing guidelines

Thank you for your interest in contributing to EvalAI! Here are a few pointers about how you can help.

## Installation instructions

Setting up EvalAI on your local machine is really easy. You can setup EvalAI using docker:
The steps are:

1. Install [docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/install/) on your machine.

2. Get the source code on to your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
    ```

3. Build and run the Docker containers. This might take a while.

    ```
    docker-compose up --build
    ```

4. That's it. Open web browser and hit the URL [http://127.0.0.1:8888](http://127.0.0.1:8888). Three users will be created by default which are listed below -

    **SUPERUSER-** username: `admin` password: `password`  
    **HOST USER-** username: `host` password: `password`  
    **PARTICIPANT USER-** username: `participant` password: `password`

### Finding something to work on

The issue tracker of EvalAI a good place to start. If you find something that interests you, comment on the thread and we’ll help get you started.

Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. The existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., that can help you in selecting one.

If neither of these seem appealing, please post on our channel and we will help find you something else to work on.

### Instructions to submit code

Before you submit code, please talk to us via the issue tracker so we know you are working on it.

Our central development branch is development. Coding is done on feature branches based off of development and merged into it once stable and reviewed. To submit code, follow these steps:

1. Create a new branch off of development. Select a descriptive branch name.

        git fetch upstream
        git checkout master
        git merge upstream/master
        git checkout -b your-branch-name

2. Commit and push code to your branch:

    - Commits should be self-contained and contain a descriptive commit message.
        ##### Rules for a great git commit message style
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
    - Also, For Pretifying the Frontend Code Use ```HTML/JS/CSS Pretifier```.
    - For installing the Sublime Package Control Manager in Sublime-Text Editor use [this](https://packagecontrol.io/installation#st2) link. Also, If Sublime Package Control Manager is installed then install ```HTML/JS/CSS Pretifier```.

3. Once the code is pushed, create a pull request:

    - On your GitHub fork, select your branch and click “New pull request”. Select “master” as the base branch and your branch in the “compare” dropdown.
If the code is mergeable (you get a message saying “Able to merge”), go ahead and create the pull request.
    - Check back after some time to see if the Travis checks have passed, if not you should click on “Details” link on your PR thread at the right of “The Travis CI build failed”, which will take you to the dashboard for your PR. You will see what failed / stalled, and will need to resolve them.
    - If your checks have passed, your PR will be assigned a reviewer who will review your code and provide comments. Please address each review comment by pushing new commits to the same branch (the PR will automatically update, so you don’t need to submit a new one). Once you are done, comment below each review comment marking it as “Done”. Feel free to use the thread to have a discussion about comments that you don’t understand completely or don’t agree with.

    - Once all comments are addressed, the reviewer will give an LGTM (‘looks good to me’) and merge the PR.

Congratulations, you have successfully contributed to Project EvalAI!
