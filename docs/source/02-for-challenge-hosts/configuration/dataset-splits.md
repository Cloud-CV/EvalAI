# Dataset Splits

Dataset splits define the subset of test-set on which the submissions will be evaluated on. Generally, most challenges have three splits:

  1. **train_split** (Allow participants to make a large number of submissions, let them see how they are doing, and let them overfit)
  2. **test_split** (Allow a small number of submissions so that they cannot mimic test_set. Use this split to decide the winners for the challenge)
  3. **val_split** (Allow participants to make submissions and evaluate on the validation split)

  A dataset split has the following subfields:

  - **id**: Unique integer identifier for the split

  - **name**: Name of the split (it must be unique for every split)

  - **codename**: Unique id for each split. Note that the codename of a dataset split is used to map the results returned by the evaluation script to a particular dataset split in EvalAI's database. Please make sure that no two dataset splits have the same codename. Again, make sure that the dataset split's codename match with what is in the evaluation script provided by the challenge host.