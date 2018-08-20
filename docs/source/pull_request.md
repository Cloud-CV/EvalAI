# Pull Request

Contributing to EvalAI is really easy. Just follow these steps to get started.

**Step 1: Fork**

1. Fork the EvalAI repository from [the repository](https://github.com/Cloud-CV/EvalAI).

**Step 2: Selecting an issue**

1. Select a suitable issue that will be easy for you to fix. Moreover, you can also
   take the issues based on their labels. All the issues are labelled according to its difficulty.

2. After selecting an issue, ask the maintainers of the project to assign it to you and they will assign it based on its availability.

3. Once it gets assigned, [create a branch](https://git-scm.com/docs/git-checkout) from your fork’s updated master branch using the following command:
   `git checkout -b branch_name`

4. Start working on the issue.

**Step 3: Committing Your Changes**

1. After making the changes, you need to add your files to your local git repository.

2. To add your files, use the following commands:

- To add only modified files, use `git add -u`
- To add a new file, use `git add file_path_from_local_git_repository`
- To add all files, use `git add .`

3. Once you have added your files, you need to commit your changes. Always **create a very meaningful commit message related to the changes that you have done. Try to write the commit message in present imperative tense. Also namespace the commit message so that it becomes self-explanatory by just looking at the commit message.**
   For example,
   > Docs: Add verbose setup docs for ubuntu

**Step 4: Creating a [Pull Request](https://help.github.com/articles/about-pull-requests/)**

1. Before creating a Pull Request, you need to first rebase your branch with the [upstream](http://stackoverflow.com/questions/9257533/what-is-the-difference-between-origin-and-upstream-on-github) master.

2. To [rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) your branch, use following commands:
   `git fetch upstream`
   `git rebase upstream/master`

3. After rebasing, push the changes to your forked repository.
   `git push origin branch_name`

4. After pushing the code, create a Pull Request.

5. When creating a pull request, be sure to add a comment including [these](https://help.github.com/articles/closing-issues-via-commit-messages/) keywords, and also mention any maintainer to reviewing it.

**Note:**

- If you have any doubts, don't hesitate to ask in the comments. You may also add in any relevant content.
- After the maintainers review your changes, fix the code as suggested. Don't forget to add, commit, and push your code to the same branch.

Once you have completed the above steps, you have successfully created a Pull Request to EvalAI.
