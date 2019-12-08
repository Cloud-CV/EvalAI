## Contributing guidelines

Thank you for your interest in contributing to EvalAI! Here are a few pointers about how you can contribute.

### Setting things up

To set up the development environment, follow the instructions in [README](https://github.com/Cloud-CV/EvalAI-ngx/blob/master/README.md).

### Finding something to work on

The issue tracker of EvalAI a good place to start. If you find something that interests you, comment on the thread and we’ll help get you started.

Alternatively, if you come across a new bug, please file a new issue and comment if you would like to be assigned. The existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., that can help you in selecting one.

If neither of these seem appealing, please post on our [gitter channel](https://gitter.im/Cloud-CV/EvalAI) and we will help find you something else to work on.

### Instructions to submit code

Before you submit code, please talk to us via the issue tracker so we know you are working on it and also let us know your approach, to be sure that you are thinking on right direction.

Our central development branch is development. Coding is done on feature branches based off of development and merged into it once stable and reviewed. 

To submit code, follow these steps:

1. Create a new branch off of master. Select a descriptive branch name. If you have not added the upstream then run this command:

```
git remote add upstream https://github.com/Cloud-CV/EvalAI-ngx
```
and to verify :

```
git remote -v
```

The commands below will help you to get the latest version of the code from the upstream(master branch). 

```
git fetch upstream
git checkout master
git merge upstream/master
git checkout -b your-branch-name
```

2. Commit and push code to your branch:

    - Commits should be self-contained and contain a descriptive commit message.

    - Please make sure your code is well-formatted and adheres to PEP8 conventions (for Python) and the airbnb style guide (for JavaScript). For others (Lua, prototxt etc.) please ensure that the code is well-formatted and the style consistent.

    - Please ensure that your code is well tested.

    - If you have to check for any linting issues, run the following command before creating the pull request:
        ```ng lint```
    - For running the testcases locally use ```ng test``` command.
    
    - Also, For Pretifying the Frontend Code Use ```HTML/JS/CSS Pretifier```.
    
    - For installing the Sublime Package Control Manager in Sublime-Text Editor use [this](https://packagecontrol.io/installation#st2) link. Also, If Sublime Package Control Manager is installed then install ```HTML/JS/CSS Pretifier```.
3. Once the code is pushed, create a pull request:
    - On your Github fork, select your branch and click “New pull request”. Select “master” as the base branch and your branch in the “compare” dropdown.
      If the code is mergeable (you get a message saying “Able to merge”), go ahead and create the pull request.
      
    - Check back after some time to see if the Travis checks have passed, if not you should click on “Details” link on your PR thread at the right of “The Travis CI build failed”, which will take you to the dashboard for your PR. You will see what failed / stalled, and will need to resolve them.
    
    - If your checks have passed, your PR will be assigned a reviewer who will review your code and provide comments. Please address each review comment by pushing new commits to the same branch (the PR will automatically update, so you don’t need to submit a new one). Once you are done, comment below each review comment marking it as “Done”. Feel free to use the thread to have a discussion about comments that you don’t understand completely or don’t agree with.
    - Once all comments are addressed, the reviewer will give an LGTM (‘looks good to me’) and merge the PR.

4. Rules for great commit messages:
    
    - Write your commit message in the imperative: "Fix bug" and not "Fixed bug" or "Fixes bug."
    
    - Bullet points are frequently used, typically a hyphen(-) or asterisk(*) is used for the bullet.
    
    - A proper commit message should always be able to complete this sentence: "If applied, this commit will <your commit message here>"
    
    - Do not end the subject line with a period
    
    - Capitalize the subject line and each paragraph
    
    - Do not assume the reviewer understands what the original problem was.
    
    - Describe why a change is being made.
    
5. Commit message is important as it should answers/should do the following:
    
    - How does it address the issue?
    
    - What effects does the patch have?
    
    - hints at improved code structure.
    
    - Describe limitations of the current code.
    
    - The reader should properly understand why the necessary changes were made.
    
    - Commit messages are crucial as they are a concise explanation of what upgrades have been made.
    
6. Examples of great commit messages:

    - Add CPU arch filter scheduler support

    - Fix crash issue
    
    - Change design template
    
***Congratulations, you have successfully contributed to Project EvalAI!***
