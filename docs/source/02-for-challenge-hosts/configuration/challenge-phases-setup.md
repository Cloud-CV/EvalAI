# Challenge Phases Setup

Challenges on EvalAI can consist of multiple challenge phases, each representing a distinct stage in the evaluation lifecycle, such as development, validation, or testing. Each phase defines its own timeline, visibility settings, evaluation criteria, and submission rules.

Challenge phases are defined under the `challenge_phases` key in `challenge_config.yaml`.

## Challenge Phase
Each challenge phase in a challenge contains the following subfields:

### Phase Metadata

- **`id` (required)**

  **Type**: `integer`

  **Description**: Unique identifier for the phase. Must be positive and unique across all phases.

  **Example**:
  ```yaml
  id: 1
  ```

- **`name` (required)**

  **Type**: `string`

  **Description**: Display name for the phase, that will be shown to participants.

  **Example**:
  ```yaml
  name: "Dev Phase"
  ```

- **`description` (required)**
  **Type**: `string` (relative file path)

  **Description**: Path to a detailed description file for the phase in HTML format.

  **Example**:
  ```yaml
  description: "templates/challenge_phase_1_description.html"


- **`challenge` (required)**

  **Type**: `integer`

  **Description**: This field links the challenge phase to a specific challenge by its `id`. It’s essential when defining multiple phases under different challenges in a single config file.

  **Example**:
  ```yaml
  challenge: 1
  ```

- **`codename` (required)**

  **Type**: `string`

  **Description**: Unique id for each challenge phase. Note that the codename of a challenge phase is used to map the results returned by the evaluation script to a particular challenge phase. 

  _Note: The codename specified here should match with the codename specified in the evaluation script to perfect mapping._

  **Example**:
  ```yaml
  codename: dev
  ```

### Timeline

- **`start_date` (required)**

  **Type**: `datetime (UTC)`
  
  **Format**: `YYYY-MM-DD HH:MM:SS`

  **Description**: When the challenge phase opens.

  **Example**:
  ```yaml
  start_date: "2025-07-01 00:00:00"
  ```

- **`end_date` (required)**

  **Type**: `datetime (UTC)`
  
  **Format**: `YYYY-MM-DD HH:MM:SS`

  **Description**: When the challenge phase closes.

  **Example**:
  ```yaml
  end_date: "2025-09-01 23:59:59"
  ```

### Phase Settings

- **`leaderboard_public` (optional)**

  **Type**: `boolean`

  **Default**: `False`

  **Description**: Whether to keep leaderboard public or private for this phase.

  **Value**:
  - `True`: Leaderboard is public and visible to all participants.
  - `False`: Leaderboard is private and not visible.

  **Example**:
  ```yaml
  leaderboard_public: True
  ```

- **`is_public` (optional)**

  **Type**: `boolean`

  **Default**: `False`

  **Description**: Defines whether the phase is visible to participants.

  **Value**:
  - `True`: Phase is visible to all participants.
  - `False`: Phase is private and not visible to participants.

  **Example**:
  ```yaml
  is_public: False
  ```

- **`is_active` (required)**

  **Type**: `boolean`

  **Description**: Specifies whether this challenge phase is currently active. Only one phase should be active at a time during a challenge, and EvalAI uses this field to determine which phase should accept submissions.

  **Value**:
  - `True`: This phase is currently active.
  - `False`: This phase is inactive.

  **Example**:
  ```yaml
  is_active: True
  ```

- **`is_submission_public` (required)**

  **Type**: `boolean`

  **Default**: `False`

  **Description**: Defines whether the submissions are by default public or private. 
  
  _Note: This will only work when the `leaderboard_public` property is set to `True`._

  **Value**:
  - `True`: Submissions of this phase are public by default.
  - `False`: Submission of this phase are private by default.

  **Example**:
  ```yaml
  is_submission_public: True
  ```

- **`disable_logs` (optional)**

  **Type**: `boolean`

  **Description**: Defines whether the logs from this phase will be shown to participants.
  
  **Value**:
  - `True`: Logs of this phase are NOT shown to participants.
  - `False`: Logs of this phase are shown to participants.

  **Example**:
  ```yaml
  disable_logs: True
  ```

- **`allowed_email_ids` (required)**

  **Type**: `list of strings`

  **Description**: A list of email IDs allowed to participate in the challenge. Leave blank if everyone is allowed to participate.
  (e.g. `["example1@domain1.com", "example2@domain2.org", "example3@domain3.com"]` Only the participants with these email ids will be allowed to participate.) 

  **Example**:
  ```yaml
  allowed_email_ids: []
  ```

### Submission Rules

- **`max_submissions_per_day` (optional)**

  **Type**: `integer`

  **Default**: `100000`

  **Description**: Defines the maximum number of submissions allowed per day to a challenge phase. 

  **Example**:
  ```yaml
  max_submissions_per_day: 100
  ```

- **`max_submissions_per_month` (optional)**

  **Type**: `integer`

  **Default**: `100000`

  **Description**: Defines the maximum number of submissions allowed per month to a challenge phase. 

  **Example**:
  ```yaml
  max_submissions_per_month: 2000
  ```

- **`max_submissions` (optional)**

  **Type**: `integer`

  **Default**: `100000`

  **Description**: Defines the maximum number of total submissions that can be made to the challenge phase. 

  **Example**:
  ```yaml
  max_submissions: 5000
  ```

- **`max_concurrent_submissions_allowed` (optional)**

  **Type**: `integer`

  **Description**: Max number of submissions allowed in parallel at any given time.

  **Example**:
  ```yaml
  max_concurrent_submissions_allowed: 5
  ```

- **`allowed_submission_file_types` (optional)**

  **Type**: `string` (String of comma separated ext.)

  **Description**: Restrict submission formats by file extension.

  **Example**:
  ```yaml
  allowed_submission_file_types: ".json, .zip, .csv, .tsv, .h5, .npy"
  ```

- **`is_restricted_to_select_one_submission` (optional)**

  **Type**: `boolean`

  **Default**: `False`

  **Description**: Defines whether to restrict a user to select only one submission for the leaderboard.

  **Example**:
  ```yaml
  is_restricted_to_select_one_submission: True
  ```

### Submission Metadata

- **`default_submission_meta_attributes` (optional)**

  **Type**: `list[Object]`

  **Description**: The default attributes that are shown for every submission. You can toggle their visibility.

  **Example**:
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

- **`submission_meta_attributes` (optional)**

  **Type**: `list[Object]`

  **Description**: These are custom metadata fields participant can add to their submission.

  **Example**:
  ```yaml
  submission_meta_attributes:
    - name: TextAttribute
      description: "Short text info"
      type: text
      required: False
    - name: SingleOptionAttribute
      description: "Choose one"
      type: radio
      options: ["A", "B", "C"]
    - name: MultipleChoiceAttribute
      description: "Select many"
      type: checkbox
      options: ["alpha", "beta", "gamma"]
    - name: TrueFalseField
      description: "Is this final?"
      type: boolean
      required: True
  ```

### Evaluation Setup

- **`test_annotation_file` (required)**

  **Type**: `string` (relative file path)

  **Description**: The file that will be used for ranking the submission made by a participant. An annotation file can be shared by more than one challenge phase.

  **Example**:
  ```yaml
  test_annotation_file: "annotations/test_annotations_devsplit.json"
  ```

- **`is_partial_submission_evaluation_enabled` (optional)**

  **Type**: `boolean`

  **Description**: Defines whether partial submission evaluation is enabled.

  **Value**: 
  - `True`: Evaluation of partial submission is enabled.
  - `False`: Evaluation of partial submission is not enabled.

  **Example**:
  ```yaml
  is_partial_submission_evaluation_enabled: False
  ```

## Challenge Phase Splits

A challenge phase split defines the relationship between:

- A specific challenge phase (challenge_phase_id)

- A dataset split (dataset_split_id)

- A leaderboard (leaderboard_id)

This mapping allows the challenge hosts to control visibility, sorting, and presentation of submission results for each phase and split.

### Mapping

- **`challenge_phase_id` (required)**

  **Type**: `integer`

  **Description**: ID of the challenge phase to map with (must match an entry in challenge_phases).

  **Example**:
  ```yaml
  challenge_phase_id: 1
  ```

- **`leaderboard_id` (required)**

  **Type**: `integer`

  **Description**: ID of the leaderboard to map with (must match an entry in leaderboards).

  **Example**:
  ```yaml
  leaderboard_id: 1
  ```

- **`dataset_split_id` (required)**

  **Type**: `integer`

  **Description**:  ID of the dataset split to map with (must match an entry in dataset_splits).

  **Example**:
  ```yaml
  dataset_split_id: 1
  ```

  To read more about Dataset Splits <a href="./dataset-splits.html">click here</a>.

### Visibility Settings

- **`visibility` (optional)**

  **Type**: `integer`

  **Default**: `3`

  **Description**:  It will set the visibility of the numbers corresponding to metrics for this `challenge_phase_split`.

  **Value**:
  - `1`: Visible only to challenge hosts
  - `2`: Visible to challenge hosts and participants who submitted.
  - `3`: Visible to everyone on the leaderboard

  **Example**:
  ```yaml
  visibility: 2
  ```

### Leaderboard Settings

- **`leaderboard_decimal_precision` (optional)**

  **Type**: `integer`

  **Default**: `2`

  **Description**: Number of decimal places for leaderboard metrics.

  **Example**:
  ```yaml
  leaderboard_decimal_precision: 3
  ```

- **`is_leaderboard_order_descending` (optional)**

  **Type**: `boolean`

  **Default**: `True`

  **Description**: Defines the default leaderboard sorting order. It is useful in cases where you have error as a metric and want to sort the leaderboard in increasing order of error value.

  **Value**:
  - `True`: For use cases when higher is better (e.g., accuracy)
  - `False`: For use cases when lower is better (e.g., error rate)

  **Example**:
  ```yaml
  is_leaderboard_order_descending: True
  ```

- **`show_execution_time`**

  **Type**: `boolean`

  **Description**: Defines whether the submission’s execution time is displayed on the leaderboard for this split.

  **Value**:
  - `True`: Display execution time of submissions on leaderboard.
  - `False`: Hide execution time from leaderboard.

  **Example**:
  ```yaml
  show_execution_time: True
  ```

- **`show_leaderboard_by_latest_submission`**

  **Type**: `boolean`

  **Description**: Determines whether the leaderboard should be sorted by the latest submission for this split.

  **Value**:
  - `True`: Leaderboard displays scores based on latest submission.
  - `False`: Leaderboard displays scores based on the best submission by default.

  **Example**:
  ```yaml
  show_leaderboard_by_latest_submission: True
  ```

#### Example:
This is how the challenge phases setup in the challenge configuration YAML file of a sample challenge with all the above fields look like:

```yaml
challenge_phases:
  - id: 1
    name: Dev Phase
    description: templates/challenge_phase_1_description.html
    leaderboard_public: False
    is_public: True
    challenge: 1
    is_active: True
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: False
    is_submission_public: True
    start_date: 2025-07-01 00:00:00
    end_date: 2025-08-31 23:59:59
    test_annotation_file: annotations/test_annotations_devsplit.json
    codename: dev
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: True
      - name: method_description
        is_visible: True
    submission_meta_attributes:
      - name: TextAttribute
        description: Sample
        type: text
        required: False
      - name: SingleOptionAttribute
        description: Sample
        type: radio
        options: ["A", "B", "C"]
    is_restricted_to_select_one_submission: False
    is_partial_submission_evaluation_enabled: False
    allowed_submission_file_types: ".json, .zip"
  
  - id: 2
    name: Test Phase
    description: templates/challenge_phase_2_description.html
    leaderboard_public: True
    is_public: True
    challenge: 2
    is_active: True
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: False
    is_submission_public: True
    start_date: 2019-01-01 00:00:00
    end_date: 2099-05-24 23:59:59
    test_annotation_file: annotations/test_annotations_testsplit.json
    codename: test
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 50
    default_submission_meta_attributes:
      - name: method_name
        is_visible: True
      - name: method_description
        is_visible: True
      - name: project_url
        is_visible: True
      - name: publication_url
        is_visible: True
    submission_meta_attributes:
      - name: TextAttribute
        description: Sample
        type: text
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
    is_restricted_to_select_one_submission: False
    is_partial_submission_evaluation_enabled: False

challenge_phase_splits:
  - challenge_phase_id: 1
    leaderboard_id: 1
    dataset_split_id: 1
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: True
    show_execution_time: True
    show_leaderboard_by_latest_submission: True
  - challenge_phase_id: 2
    leaderboard_id: 1
    dataset_split_id: 1
    visibility: 3
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: True
    showeceution_time: False
    show_leaderboard_by_latest_submission: False
  - challenge_phase_id: 2
    leaderboard_id: 1
    dataset_split_id: 2
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: True
    show_execution_time: True
    show_leaderboard_by_latest_submission: True
```