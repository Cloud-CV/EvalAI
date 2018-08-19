
## Challenge creation

Creating a challenge on EvalAI is really easy. You just need to follow the following three steps and we will take care of the rest. To make life easier for the challenge hosts, we provide a sample challenge configuration that you can use to get started. Fork and clone [EvalAI-Starters](https://github.com/cloud-CV/evalai-starters) repository to start.

#### 1. Create challenge configuration file 
___

First of all, open the [`challenge_config.yml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) if you have cloned the [EvalAI-Starters](https://github.com/cloud-CV/evalai-starters) repository or create one. This file will define the start date, end date, number of phases and many more details of the challenge. Start editing this file according to your needs. For reference to the fields, refer to the following description:


* **title**: Title of the challenge

* **short_description**: Short description of the challenge (preferably 140 characters max)

* **description**: Long description of the challenge (use a relative path for the HTML file, e.g. `challenge_details/description.html`)

* **evaluation_criteria**: Evaluation criteria and details of the challenge (use a relative path for the HTML file, e.g. `challenge_details/evaluation.html`)

* **terms_and_conditions**: Terms and conditions of the challenge (use a relative path for the HTML file, e.g. `challenge_details/tnc.html`)

* **image**: Logo of the challenge (use a relative path for the logo in the zip configuration, e.g. `images/logo/challenge_logo.jpg`). **Note**: The image must be in jpg, jpeg or png format.

* **submission_guidelines**: Submission guidelines of the challenge (use a relative path for the HTML file, e.g. `challenge_details/submission_guidelines.html`)

* **evaluation_script**: The evaluation script using which the submissions will be evaluated (path of the evaluation script file or folder relative to this YAML file.)

* **remote_evaluation**: True/False (specify whether evaluation will happen on private machine or not. Default is `False`)

* **start_date**: Start DateTime of the challenge (Format: YYYY-MM-DD HH:MM:SS, e.g. 2017-07-07 10:10:10) in `UTC` timezone

* **end_date**: End DateTime of the challenge (Format: YYYY-MM-DD HH:MM:SS, e.g. 2017-07-07 10:10:10) in `UTC` timezone

* **published**: True/False (a Boolean field that gives the flexibility to publish the challenge once approved by EvalAI Admin. Default is `False`)

* **allowed_email_domains**: A list of domains allowed to participate in the challenge. Leave blank if everyone is allowed to participate. (e.g. `["domain1.com", "domain2.org", "domain3.in"]` Participants in these email domains will only be allowed to participate.)

* **blocked_emails_domains**: A list of domains not allowed to participate in the challenge. Leave blank if everyone is allowed to participate. (e.g. `["domain1.com", "domain2.org", "domain3.in"]` The participants with these email domains will not be allowed to participate.)

* **leaderboard**:
  A leaderboard for a challenge on EvalAI consists of following subfields:

  * **id**: Unique integer field for each leaderboard entry

  * **schema**: Schema field contains the information about the rows of the leaderboard. A schema contains two keys in the leaderboard:

    1. `labels`: Labels are the header rows in the leaderboard according to which the challenge ranking is done.

    2. `default_order_by`: This key decides the default sorting of the leaderboard based on one of the labels defined above.

  The leaderboard schema for the sample challenge configuration given [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) looks like this:

  ```yaml
  leaderboard:
    - id: 1
      schema: { "labels": ["Metric1", "Metric2", "Metric3", "Total"], "default_order_by": "Total" }
  ```

  The above schema of the leaderboard for Random Number Generator Challenge creates the leaderboard web interface like this:

  ![Leaderboard](_static/img/leaderboard.png "Random Number Generator Challenge - Leaderboard")

* **challenge_phases**:

  There can be multiple challenge phases in a challenge. A challenge phase in a challenge contains the following subfields:

    * **id**: Unique integer identifier for the challenge phase

    * **name**: Name of the challenge phase

    * **description**: Long description of the challenge phase (set the relative path of the HTML file, e.g. `challenge_details/phase1_description.html`)

    * **leaderboard_public**: True/False (a Boolean field that gives the flexibility to Challenge Hosts to either make the leaderboard public or private. Default is `False`)

    * **is_public**: True/False (a Boolean field that gives the flexibility to Challenge Hosts to either hide or show the challenge phase to participants. Default is `False`)

    * **is_submission_public**: True/False (a Boolean field that gives the flexibility to Challenge Hosts to either make the submissions by default public/private. Note that this will only work when the `leaderboard_public` property is set to true. Default is `False`)

    * **start_date**: Start DateTime of the challenge phase (Format: YYYY-MM-DD HH:MM:SS, e.g. 2017-07-07 10:10:10)

    * **end_date**: End DateTime of the challenge phase (Format: YYYY-MM-DD HH:MM:SS, e.g. 2017-07-07 10:10:10)

    * **test_annotation_file**: This file is used for ranking the submission made by a participant. An annotation file can be shared by more than one challenge phase. (Path of the test annotation file relative to this YAML file, e.g. `challenge_details/test_annotation.txt`)

    * **codename**: Challenge phase codename. Note that the codename of a challenge phase is used to map the results returned by the evaluation script to a particular challenge phase. The codename specified here should match with the codename specified in the evaluation script to perfect mapping.

    * **max_submissions_per_day**: Positive integer which tells the maximum number of submissions per day to a challenge phase.

    * **max_submissions**: a Positive integer that decides the overall maximum number of submissions that can be done to a challenge phase.

* **dataset_splits**:

  Many of the AI challenges are based on static datasets. A dataset related to a challenge generally has 3 dataset splits:

  1. Training set
  2. Validation set
  3. Test set

  While creating splits for a challenge, you can have any number of splits where you can use some splits for checking if some participant team is cheating or not by doing some extra analysis on that split. The possibilities are endless.

  A dataset split has the following subfields:

  * **id**: Unique integer identifier for the dataset split

  * **name**: Name of the dataset split (it must be unique for every dataset split)

  * **codename**: Codename of dataset split. Note that the codename of a dataset split is used to map the results returned by the evaluation script to a particular dataset split in EvalAI's database. Please make sure that no two dataset splits have the same codename. Again, make sure that the dataset split's codename match with what is in the evaluation script provided by the challenge host.

* **challenge_phase_splits**:

  A challenge phase split is a relation between a challenge phase and dataset splits for a challenge (many to many relation). This is used to set the privacy of submissions (public/private) to different dataset splits for different challenge phases.

  * **challenge_phase_id**: Id of challenge_phase (Gets the challenge phase details to map with)

  * **leaderboard_id**: Id of leaderboard (Given above)

  * **dataset_split_id**: Id of dataset split (Given above)

  * **visibility**: Enter any of the positive integers given below.

    - HOST: 1

    - OWNER AND HOST: 2

    - PUBLIC: 3

#### 2. Write evaluation script
---

Please refer to the [writing evaluation script section](evaluation_scripts.html) to know more.

#### 3. Add challenge details and upload
---

We are almost there. Now, you just need to update the HTML templates. EvalAI supports all kinds of HTML tags which means you can add images, videos, tables etc. Moreover, you can add inline CSS to add custom styling to your challenge details.

#### Next Steps
---

The next step is to create a zip file that contains the YAML config file, all the HTML templates for the challenge description, challenge phase description, evaluation criteria, submission guidelines, evaluation script, test annotation file(s) and challenge logo (optional).

The final step is to create a challenge host team for the challenge on EvalAI. After that, just upload the zip folder created in the above steps and the challenge will be created.

If you have issues in creating a challenge on EvalAI, please feel free to create an issue on our [Github Issues Page](https://github.com/Cloud-CV/EvalAI/issues/new).

#### How to approve a challenge?
---

Once a challenge config has been uploaded, the challenge has to be approved by the EvalAI Admin (i.e you if you are hosting your own version of EvalAI) to make it available to the public. Please follow the following steps to make the challenge public:

Let's take a sample challenge with name `Random Number Generator Challenge`.

##### Step 1: Approve challenge using Django Admin

1. Login to EvalAI's django admin using http://localhost:8000/admin/challenges/challenge/, and you will see the list of challenges
    ![](https://i.imgur.com/FRi5ofa.png)


2. Click on the challenge that you want to approve and scroll to bottom to check the following two fields.
    * Approved By Admin

    ![](https://i.imgur.com/l7fQrxX.png)

    Now, save the challenge.

**Challenge has been successfully approved by the administrator and is also visible to users.**

##### Step 2: Reload Submission Worker

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

## Challenge configuration examples

Please see this [repository](https://github.com/Cloud-CV/EvalAI-Examples) to see different types of challenge configurations you can have for your challenge.

## Create challenge using web interface

Todo: We are working on this feature and will keep you updated.
