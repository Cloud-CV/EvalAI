# Getting started with EvalAI Issues:

To contribute for CloudCV in EvalAI is a facile task. Please follow these steps in order to get started :-)

**Step 1 : Fork**

1. Fork the EvalAI repository from [this](https://github.com/Cloud-CV/EvalAI) link.

**Step 2 : Picking up a issue:**

1. Pick up a suitable issue that you find will be facile for you to fix. Moreover, you can also 
take the issues based on their labels. Almost every issue is marked with a label according to its difficulty.

2. After selecting any issue, mention any mentor’s name there and ask him to assign it to you.

3. Once it gets assigned , create a branch from your fork’s updated master branch using the command :-
`git checkout -b branch_name`
**Note:** To know more about the `checkout` command command, please refer to [this](https://git-scm.com/docs/git-checkout) link.

4. Start working on the issue.

**Step 3: Committing Your Changes:**

1. After making the required feature as asked in the issue, you need to add your files to local git repository.

2. If you want to create any migration file then use this command to create the migration file.
`python manage.py makemigrations app_name --name=suitable_name --settings=settings.dev`

3. To add your files , these commands can be handy:

- To add only modified files `git add -u`
- To add a new file `git add file_path_from_local_git_repository`
- To add all files `git add .`

4. Once you have added your files, you need to commit your changes. Always **create a very meaningful commit message related to the feature that you have added.**

**Step 4: Creating a Pull Request:**

**Note:** To know more about **Pull Request**, please refer to [this](https://help.github.com/articles/about-pull-requests/) link.

1. Before creating a Pull Request, you need to first rebase your branch with the upstream master.
**Note:** To know more about **upstream**, please refer to [this](http://stackoverflow.com/questions/9257533/what-is-the-difference-between-origin-and-upstream-on-github) link.

2. To rebase your branch, execute these commands:
`git fetch upstream`
`git rebase upstream/master`
**Note:** To know about **rebase**, please read [this](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) link.

3. After rebasing, forcefully push the changes on your forked repository.
`git push -f origin branch_name`

4. After pushing the code, create a Pull Request.

5. At the time of creation of Pull Request, create a comment with [these](https://help.github.com/articles/closing-issues-via-commit-messages/) keywords and also mention any mentor’s name for reviewing it.

**Note:** 

- If you find that there is some relevant content to be mentioned or any doubts to be asked, then also mention these things in the comment.
- After the reviews from the mentor, fix the changes as suggested & push the code on the same branch after adding & committing.

Once you complete the above steps, you have successfully created your first Pull Request to EvalAI.
