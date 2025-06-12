# Phases Setup

There can be multiple [challenge phases](https://evalai.readthedocs.io/en/latest/glossary.html#challenge-phase) in a challenge. A challenge phase in a challenge contains the following subfields:

  - **id**: Unique integer identifier for the challenge phase

  - **name**: Name of the challenge phase

  - **description**: Long description of the challenge phase (set the relative path of the HTML file, e.g. `templates/challenge_phase_1_description.html`)

  - **leaderboard_public**: True/False (a Boolean field that gives the flexibility to Challenge Hosts to either make the leaderboard public or private. Default is `False`)

  - **is_public**: True/False (a Boolean field that gives the flexibility to Challenge Hosts to either hide or show the challenge phase to participants. Default is `False`)

  - **is_submission_public**: True/False (a Boolean field that gives the flexibility to Challenge Hosts to either make the submissions by default public/private. Note that this will only work when the `leaderboard_public` property is set to true. Default is `False`)

  - **start_date**: Start DateTime of the challenge phase (Format: YYYY-MM-DD HH:MM:SS, e.g. 2017-07-07 10:10:10)

  - **end_date**: End DateTime of the challenge phase (Format: YYYY-MM-DD HH:MM:SS, e.g. 2017-07-07 10:10:10)

  - **test_annotation_file**: This file is used for ranking the submission made by a participant. An annotation file can be shared by more than one challenge phase. (Path of the test annotation file relative to this YAML file, e.g. `annotations/test_annotations_devsplit.json`)

  - **codename**: Unique id for each challenge phase. Note that the codename of a challenge phase is used to map the results returned by the evaluation script to a particular challenge phase. The codename specified here should match with the codename specified in the evaluation script to perfect mapping.

  - **max_submissions_per_day**: A positive integer that tells the maximum number of submissions per day to a challenge phase. (Optional, Default value is `100000`)

  - **max_submissions_per_month**: A positive integer that tells the maximum number of submissions per month to a challenge phase. (Optional, Default value is `100000`)

  - **max_submissions**: A positive integer that decides the maximum number of total submissions that can be made to the challenge phase. (Optional,  Default value is `100000`)

  - **default_submission_meta_attributes**: These are the default metadata attributes that will be displayed for all submissions, the metadata attributes are `method_name`, `method_description`, `project_url`, and `publication_url`.
      ```yaml
    default_submission_meta_attributes:
      - name: method_name
        is_visible: True
      - name: method_description
        is_visible: True
      - name: project_url
        is_visible: True
      - name: publication_url
        is_visible: True
      ```
  - **submission_meta_attributes**: These are the custom metadata attributes that participants can add to their submissions. The custom metadata attributes are `TextAttribute`, `SingleOptionAttribute`, `MultipleChoiceAttribute`, and `TrueFalseField`.
    ```yaml
    submission_meta_attributes:
      - name: TextAttribute
        description: Sample
        type: text
        required: False
      - name: SingleOptionAttribute
        description: Sample
        type: radio
        options: ["A", "B", "C"]
      - name: MultipleChoiceAttribute
        description: Sample
        type: checkbox
        options: ["alpha", "beta", "gamma"]
      - name: TrueFalseField
        description: Sample
        type: boolean
        required: True
    ```
  - **is_restricted_to_select_one_submission**: True/False (indicates whether to restrict a user to select only one submission for the leaderboard. Default is `False`)
  - **is_partial_submission_evaluation_enabled**: True/False (indicates whether partial submission evaluation is enabled. Default is `False`)
  - **allowed_submission_file_types**: This is a list of file types that are allowed for submission (Optional Default is `.json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy`)
