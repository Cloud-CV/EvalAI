# Pull Request

Contributing to EvalAI is a facile task. Please follow these steps in order to get started.

**Step 1 : Fork**

1. Fork the EvalAI repository from [EvalAI](https://github.com/Cloud-CV/EvalAI) link.

**Step 2 : Picking up a issue**

1. Pick up a suitable issue that you find will be easy for you to fix. Moreover, you can also pick the issues based on their labels. All issues are marked with a label according to its difficulty.

2. After selecting any issue, ask the maintainers of the project to assign it to you and they will assign it based on its availability.

3. Once it gets assigned , [create](https://git-scm.com/docs/git-checkout) a branch from your fork’s updated master branch using the following command
`git checkout -b branch_name`

4. Start working on the issue.

**Step 3: Committing Your Changes**

1. After making the required feature as asked in the issue, you need to add your files to local git repository.

2. To add your files , following commands can be handy

- To add only modified files `git add -u`
- To add a new file `git add file_path_from_local_git_repository`
- To add all files `git add .`

3. Once you have added your files, you need to commit your changes. Always **create a very meaningful commit message related to the feature that you have added. Try to write the commit message in present imperative tense. Also namespace the commit message so that it becomes self explanatory by just looking at the commit message.**
for example, 
> Docs: Add verbose setup docs for ubuntu

**Step 4: Creating a [Pull Request](https://help.github.com/articles/about-pull-requests/)**

1. Before creating a Pull Request, you need to first rebase your branch with the [upstream](http://stackoverflow.com/questions/9257533/what-is-the-difference-between-origin-and-upstream-on-github) master.

2. To [rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) your branch, use following commands
`git fetch upstream`
`git rebase upstream/master`

3. After rebasing, push the changes on your forked repository.
`git push origin branch_name`

4. After pushing the code, create a Pull Request.

5. At the time of creation of Pull Request, create a comment with [these](https://help.github.com/articles/closing-issues-via-commit-messages/) keywords and also mention any maintainers name for reviewing it.

**Note:** 

- If you find that there is some relevant content to be mentioned or any doubts to be asked, then also mention these things in the comment.
- After the reviews from the maintainer, fix the changes as suggested and push the code on the same branch after committing.

Once you complete the above steps, you have successfully created a Pull Request to EvalAI.
