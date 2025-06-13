# Dataset Splits

Dataset splits define the subset of test-set on which the submissions will be evaluated on. Generally, most challenges have three splits:

  1. **train_split** (Allow participants to make a large number of submissions, let them see how they are doing, and let them overfit)
  2. **test_split** (Allow a small number of submissions so that they cannot mimic test_set. Use this split to decide the winners for the challenge)
  3. **val_split** (Allow participants to make submissions and evaluate on the validation split)

A dataset split has the following subfields:

- **`id` (required)**

  **Type**: `integer`

  **Description**: Unique numeric identifier for the dataset split. Used internally to reference this split in phase-split mappings.

  **Example**:
  ```yaml
  id: 1
  ```

- **`name` (required)**

  **Type**: `string`

  **Constraints**: Must be unique.

  **Description**: Human-readable name of the dataset split. This will be shown in the EvalAI UI and should clearly describe the split's purpose.

  **Example**:
  ```yaml
  name: Train Split
  ```

- **`codename` (required)**

  **Type**: `string`

  **Constraints**: Must be unique and must match the codename used in the evaluation script.

  **Description**: A unique identifier used to map evaluation results to the correct dataset split. This is critical for EvalAI to interpret the scores returned by your evaluation script.

  **Example**:
  ```yaml
  codename: train_split
  ```

  #### Example

  Here’s how the dataset splits configuration will look like in `challenge_config.yaml` file of a sample challenge:

  ```yaml
  dataset_splits:
    - id: 1
      name: Train Split
      codename: train_split
    - id: 2
      name: Test Split
      codename: test_split
    - id: 3
      name: Validation Split
      codename: val_split
  ```