## How to approve a challenge?

Once a challenge config has been uploaded, the challenge has to be approved by the EvalAI Admin (i.e you if you are hosting your own version of EvalAI) to make it available to everyone. Please follow the following steps to approve a challenge:

Let's assume that we want to approve a challenge with name `Random Number Generator Challenge`.

### Step 1: Approve challenge using Django Admin

1. Login to EvalAI's [django admin panel](http://localhost:8000/admin/challenges/challenge/), and you will see the list of challenges
    ![](https://i.imgur.com/FRi5ofa.png)

2. Click on the challenge that you want to approve and scroll to bottom to check the following two fields.
    * Approved By Admin
    * Publically Available

    ![](https://i.imgur.com/l7fQrxX.png)

    Now, save the challenge. The challenge has been successfully approved by the administrator and is also publicly visible to the users.

### Step 2: Reload Submission Worker

Submission worker is a key component of EvalAI. Since you have recently approved the challenge, the submission worker has to be reloaded so that it can fetch the evaluation script and other related files for your challenge. Now reload the submission worker using the following command:

Run the following command:

    docker-compose restart worker 

**Submission worker has been successfully reloaded!**

Now, the challenge is ready for accepting submissions by participants.

If you have issues in hosting a challenge on EvalAI Forked version, please feel free to create an issue on our [Github Issues Page](https://github.com/Cloud-CV/EvalAI/issues/new).
