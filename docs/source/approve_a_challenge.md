## How to approve a challenge?

Once a challenge config has been uploaded, the challenge has to be approved by the EvalAI Admin (i.e you if you are hosting your own version of EvalAI) to make it available to the public. Please follow the following steps to make the challenge public:

Let's take a sample challenge with name `Random Number Generator Challenge`.

#### Step 1: Approve challenge using Django Admin

1. Login to EvalAI's django admin using http://localhost:8000/admin/challenges/challenge/, and you will see the list of challenges
    ![](https://i.imgur.com/FRi5ofa.png)


2. Click on the challenge that you want to approve and scroll to bottom to check the following two fields.
    * Approved By Admin

    ![](https://i.imgur.com/l7fQrxX.png)

    Now, save the challenge.

**Challenge has been successfully approved by the administrator and is also visible to users.**

#### Step 2: Reload Submission Worker

Submission worker is a key component of EvalAI. Since you have recently approved the challenge, the submission worker has to be reloaded so that it can fetch the evaluation script and other related files for your challenge. Now reload the submission worker using the following command:

Run the following command if you are using docker-compose setup:

    docker-compose reload worker 

If you are using virtual environment, then please go through the following instructions:

Kill the previous submission worker process and spawn a new one.

1. Find the submission worker process id's by using the below command

    `ps aux | grep scripts/workers/submission_worker.py`

    ![](https://i.imgur.com/Iv34zEM.png)

    Since there are three processes running (Shown in red     box). Also notice the process id's of all the three       workers (Shown in yellow box).

2. Kill all the existing workers by using the below commads.

    `kill <processid>`
    
    OR
    
     `kill $(ps aux | grep '[p]ython scripts/workers/submission_worker.py' | awk '{print $2}')`
    
    ![](https://i.imgur.com/m95X6WR.png)
     
3. Now restart all the workers again by using the command

    `python scripts/workers/submission_worker.py`

**Submission worker has been successfully reloaded!**

Now, the challenge is ready for accepting submissions by participants.

If you have issues in hosting a challenge on EvalAI Forked version, please feel free to create an issue on our [Github Issues Page](https://github.com/Cloud-CV/EvalAI/issues/new).
