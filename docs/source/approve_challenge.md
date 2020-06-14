## Approve a challenge (for forked version)

**Note:** If you are hosting the challenge on [evalai.cloudcv.org](https://evalai.cloudcv.org), then you cannot approve your challenge. It will be approved by [EvalAI team](https://evalai.cloudcv.org/team). You can skip this section.

Once a challenge config has been uploaded, the challenge has to be approved by the EvalAI Admin (i.e. you if you are setting up EvalAI yourself on your server) to make it available to everyone. Please follow the following steps to approve a challenge (if you are ):

Let's assume that we want to approve a challenge with name `Random Number Generator Challenge`.

### Step 1: Approve challenge using django admin

1. Login to EvalAI's [django admin panel](http://localhost:8000/admin/challenges/challenge/), and you will see the list of challenges

   ![](https://i.imgur.com/FRi5ofa.png)

2. Click on the challenge that you want to approve and scroll to bottom to check the following two fields.

   - Approved By Admin
   - Publically Available

   ![](https://i.imgur.com/l7fQrxX.png)

   Now, save the challenge. The challenge has been successfully approved by the administrator and is also publicly visible to the users.

### Step 2: Reload submission worker

Since you have just approved the challenge, the submission worker has to be reloaded so that it can fetch the evaluation script and other related files for your challenge from the database. Now reload the submission worker using the following command:

Run the following command:

    docker-compose restart worker

**Submission worker has been successfully reloaded!**

Now, the challenge is ready to accept submissions from participants.

If you have issues in hosting a challenge on forked version of EvalAI, please feel free to create an issue on our [GitHub Issues Page](https://github.com/Cloud-CV/EvalAI/issues/new).
