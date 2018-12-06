import sys
import traceback

def evaluate(test_annotation_file ,user_annotation_file, phase_name, **kwargs):

    original_values = []
    print("Loading Test annotation file ...")
    with open(test_annotation_file, "r") as f:
        for line in f:
            original_values.append(line)
    print("Successfully loaded the test annotation file")

    user_values = []
    print("Loading User annotation file ...")
    with open(user_annotation_file, "r") as f:
        for line in f:
            user_values.append(line)
    print("Successfully loaded the User annotation file")

    score = set(user_values).intersection(original_values).__len__()
    result = {}
    try:
        result['result'] = [
            {
                'split1': {
                    'score': score,
                }
            },
            {
                'split2': {
                    'score': score,
                }
            }
        ]
        result['submission_metadata'] = "This submission metadata will only be shown to the Challenge Host"
        result['submission_result'] = "This is the actual result to show to the participant once submission is finished"
        return result
    except Exception as e:
        sys.stderr.write(traceback.format_exc())
        return e
