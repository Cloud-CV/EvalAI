# Editing Challenge Configuration

After a challenge has been created on EvalAI, you may need to update some fields—like changing submission limits, fixing typos, or adjusting dates. This guide explains **which fields can be edited**, **how to do updates**, and **how to test configuration changes locally**.

## Editable Fields

All the fields in the challenge configuration YAML can typically be updated, except the following:

`challenge_phase_splits` 

`dataset_splits`

In addition to this, the above two fields are **irreversible**, which means, dataset splits or phases cannot be deleted once submissions are made.

## How to Edit the fields

All the fields that are editable can be edited by either of the following two ways:

- ### Editing directly through EvalAI dashboard
    Once you create your challenge and push it successfully through the challlenge branch, your challenge will be visible on the EvalAI dashboard at `https://eval.ai`.

    Almost all of the fields, except a few, can be edited directly from the dashboard. Such fields will have an "edit" icon (a small pen icon) appearing beside them, or an "upload" sign in case that is a file upload related field.

- ### Editing through YAML file
    However, there are some editable fields like image, leaderboard public/private, etc., which cannot be edited directly through dashboard, and in such cases you can update them through YAML configuration file.

    Once, you edit the fields in the YAML file, simply push the challenge branch again and once all the checks pass, you should see the updated fields in the dashboard.

**Note:** If your challenge configuration YAML file is not in sync with the dashboard (e.g., some fields are update directly on dashboard but are still outdated in the YAML file), in such a case, pushing your YAML file to the challenge branch will result in making the dashbord fields same as the ones in YAML file.

Hence, keep your YAML file updated and in sync with the dashboard updates, before pushing the file again.

## How to test the changes locally before submission

It's best to test the changes on EvalAI's staging server `https://staging.eval.ai` before pushing your changes to the main production URL i.e., `https://eval.ai`.

To do this follow the steps mentioned below:

1. Use the EvalAI starter repository as [template](https://docs.github.com/en/free-pro-team@latest/github/creating-cloning-and-archiving-repositories/creating-a-repository-from-a-template).

2. Generate your [github personal acccess token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) and copy it in clipboard.

3. Add the github personal access token in the forked repository's [secrets](https://docs.github.com/en/free-pro-team@latest/actions/reference/encrypted-secrets#creating-encrypted-secrets-for-a-repository) with the name `AUTH_TOKEN`.

4. Now, go to [EvalAI staging server](https://staging.eval.ai) to fetch the following details -
   1. `evalai_user_auth_token` - Go to [profile page](https://staging.eval.ai/web/profile) after logging in and click on `Get your Auth Token` to copy your auth token.
   2. `host_team_pk` - Go to [host team page](https://staging.eval.ai/web/challenge-host-teams) and copy the `ID` for the team you want to use for challenge creation.
   3. `evalai_host_url` - Use `https://staging.eval.ai` for staging server.

5. Create a branch with name `challenge` in the forked repository from the `master` branch.
<span style="color:purple">Note: Only changes in `challenge` branch will be synchronized with challenge on EvalAI.</span>

6. Add `evalai_user_auth_token` and `host_team_pk` in `github/host_config.json`.

7. Read [EvalAI challenge creation documentation](./challenge-config.html) to know more about how you want to structure your challenge. Once you are ready, start making changes in the yaml file, HTML templates, evaluation script according to your need.

8. To update the challenge configuration and test it locally on staging server, make changes in the repository and push on `challenge` branch and wait for the build to complete. View the [logs of your build](https://docs.github.com/en/free-pro-team@latest/actions/managing-workflow-runs/using-workflow-run-logs#viewing-logs-to-diagnose-failures).

9. If challenge config contains errors then a `issue` will be opened automatically in the repository with the errors otherwise the challenge will be created on EvalAI Staging server.

10. Go to [Hosted Challenges](https://staging.eval.ai/web/hosted-challenges) to view your challenge on the staging server.

The challenge will be publicly available once you push it to the main production server i.e., `https://eval.ai` and admin approves the challenge.






