Contributing guidelines
-----------------------

Thank you for your interest in contributing to EvalAI! Here are a few
pointers on how you can help.

Setting things up
~~~~~~~~~~~~~~~~~

To set up the development environment, follow the instructions in
our README.

Finding something to work on
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EvalAI's issue tracker is good place to start. If you find something
that interests you, comment on the thread and we’ll help get you
started.

Alternatively, if you come across a new bug on the site, please file a
new issue and comment if you would like to be assigned. Existing
issues are tagged with one or more labels, based on the part of the
website it touches, its importance etc., which can help you select
one.

If neither of these seem appealing, please post on our channel and we
will help find you something else to work on.

Instructions to submit code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you submit code, please talk to us via the issue tracker so we
know you are working on it.

Our central development branch is `development`. Coding is done on feature
branches based off of development and merged into it once stable and
reviewed. To submit code, follow these steps:

1. Create a new branch off of development. Select a descriptive branch
   name. 
   ::
       git fetch upstream
       git checkout master
       git merge upstream/master
       git checkout -b your-branch-name

   We highly encourage using `black <http://www.github.com/psf/black>`_
   to format your code. It sticks to PEP8 for the most part and is in 
   line with the rest of the repo. We have already set up `pre-commit 
   hooks <https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks>`_
   to run black and flake8. To activate the hooks, you just need to run
   the following comamnd once:
   ::
      pre-commit install

2. Commit and push code to your branch:

   -  Commits should be self-contained and contain a descriptive commit
      message.
   -  Please make sure your code is well-formatted and adheres to PEP8
      conventions (for Python) and the airbnb style guide (for
      JavaScript). For others (Lua, prototxt etc.) please ensure that
      the code is well-formatted and the style consistent.
   -  Please ensure that your code is well tested.

      ::

          git commit -a -m “{{commit_message}}”
          git push origin {{branch_name}}

3. Once the code is pushed, create a pull request:

   -  On your GitHub fork, select your branch and click “New pull
      request”. Select “master” as the base branch and your branch in
      the “compare” dropdown. If the code is mergeable (you get a
      message saying “Able to merge”), go ahead and create the pull
      request.
   -  Check back after some time to see if the Travis checks have
      passed, if not you should click on “Details” link on your PR
      thread at the right of “The Travis CI build failed”, which will
      take you to the dashboard for your PR. You will see what failed /
      stalled, and will need to resolve them.
   -  If your checks have passed, your PR will be assigned a reviewer
      who will review your code and provide comments. Please address
      each review comment by pushing new commits to the same branch (the
      PR will automatically update, so you don’t need to submit a new
      one). Once you are done, comment below each review comment marking
      it as “Done”. Feel free to use the thread to have a discussion
      about comments that you don’t understand completely or don’t agree
      with.
   -  Once all comments are addressed, the reviewer will give an LGTM (‘looks good to me’) and merge the PR.

Congratulations, you have successfully contributed to Project EvalAI!
