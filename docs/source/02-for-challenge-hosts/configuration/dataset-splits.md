# Dataset Splits

Dataset splits define the subset of test-set on which the submissions will be evaluated on. Generally, most challenges have three splits:

  1. **train_split** (Allow participants to make a large number of submissions, let them see how they are doing, and let them overfit)
  2. **test_split** (Allow a small number of submissions so that they cannot mimic test_set. Use this split to decide the winners for the challenge)
  3. **val_split** (Allow participants to make submissions and evaluate on the validation split)

  A dataset split has the following subfields:

  - **id**: Unique integer identifier for the split

  - **name**: Name of the split (it must be unique for every split)

  - **codename**: Unique id for each split. Note that the codename of a dataset split is used to map the results returned by the evaluation script to a particular dataset split in EvalAI's database. Please make sure that no two dataset splits have the same codename. Again, make sure that the dataset split's codename match with what is in the evaluation script provided by the challenge host.

- **challenge_phase_splits**:

  A challenge phase split is a relation between a challenge phase and dataset splits for a challenge (many to many relation). This is used to set the privacy of submissions (public/private) to different dataset splits for different challenge phases.

  - **challenge_phase_id**: Id of `challenge_phase` to map with

  - **leaderboard_id**: Id of `leaderboard`

  - **dataset_split_id**: Id of `dataset_split`

  - **visibility**: It will set the visibility of the numbers corresponding to metrics for this `challenge_phase_split`. Select one of the following positive integers based on the visibility level you want: (Optional, Default is `3`)


  | Visibility | Description                                                             |
  | ---------- | ----------------------------------------------------------------------- |
  | 1          | Only visible to challenge host                                          |
  | 2          | Only visible to challenge host and participant who made that submission |
  | 3          | Visible to everyone on leaderboard                                      |

  - **leaderboard_decimal_precision**: A positive integer field used for varying the leaderboard decimal precision. Default value is `2`.

  - **is_leaderboard_order_descending**: True/False (a Boolean field that gives the flexibility to challenge host to change the default leaderboard sorting order. It is useful in cases where you have error as a metric and want to sort the leaderboard in increasing order of error value. Default is `True`)
