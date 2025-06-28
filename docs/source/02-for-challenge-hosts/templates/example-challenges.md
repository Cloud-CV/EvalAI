# Challenge Configuration Examples

This guide provides a set of fully functional examples of `challenge_config.yaml` file for common challenge setups on EvalAI. Each example illustrates a different real-world use case—ranging from single-phase challenges to multi-phase, multi-leaderboard competitions. These templates are designed to help organizers get started quickly, and understand how various components of the configuration work together.

Before using any of the following templates as your challenge configuration, make sure all the mentioned files exist in the correct paths as mentioned in different fields of the configuration. (e.g., `test_annotation_file`, `description`, etc.)

## Example 1: One Challenge, One Phase, One Leaderboard, One Phase Split

example_1_config.yaml:

```yaml
title: "Image Classification Challenge"
short_description: "Classify images into categories."
description: "templates/description.html"
evaluation_details: "templates/evaluation_details.html"
terms_and_conditions: "templates/terms_and_conditions.html"
image: "logo.jpg"
submission_guidelines: "templates/submission_guidelines.html"
leaderboard_description: "The leaderboard shows the evaluation results of your submissions based on accuracy. Higher is better."
evaluation_script: "evaluation_script.zip"
remote_evaluation: false
start_date: "2025-07-01 00:00:00"
end_date: "2025-12-01 23:59:59"
published: false
tags: 
  - image-classification
  - supervised-learning
  - computer-vision

leaderboard:
  - id: 1
    schema: {
      "labels": ["Accuracy"],
      "default_order_by": "Accuracy",
      "metadata": {
        "Accuracy": {
          "sort_ascending": false,
          "description": "Classification accuracy on the test set"
        }
      }
    }

challenge_phases:
  - id: 1
    name: Dev Phase
    description: templates/challenge_phase_1_description.html
    leaderboard_public: True
    is_public: True
    challenge: 1
    is_active: True
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: False
    is_submission_public: True
    start_date: 2025-07-01 00:00:00
    end_date: 2025-10-01 23:59:59
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
      - name: description
        description: Describe your classification method
        type: text
        required: True
      - name: model_type
        description: Select model type
        type: radio
        options: ["CNN", "Transformer", "Other"]
      - name: pre_trained
        description: Is the model pre-trained?
        type: boolean
    is_restricted_to_select_one_submission: False
    is_partial_submission_evaluation_enabled: False
    allowed_submission_file_types: ".json, .zip"

dataset_splits:
  - id: 1
    name: Test Split
    codename: test_split

challenge_phase_splits:
  - challenge_phase_id: 1
    leaderboard_id: 1
    dataset_split_id: 1
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: True
    show_execution_time: True
    show_leaderboard_by_latest_submission: True
```

## Example 2: One Challenge, One Phase, Two Leaderboards, Two Phase Splits

example_2_config.yaml:

```yaml
title: "Simple QA Challenge"
short_description: "Answer simple factual questions."
description: "templates/description.html"
evaluation_details: "templates/evaluation_details.html"
terms_and_conditions: "templates/terms_and_conditions.html"
image: "logo.jpg"
submission_guidelines: "templates/submission_guidelines.html"
leaderboard_description: "The leaderboard tracks performance based on accuracy and speed."
evaluation_script: "evaluation_script.zip"
remote_evaluation: false
start_date: "2025-10-01 00:00:00"
end_date: "2026-01-31 23:59:59"
published: false
tags: 
  - question-answering
  - qa
  - text

leaderboard:
  - id: 1
    schema: {
      "labels": ["Correct Answers"],
      "default_order_by": "Correct Answers",
      "metadata": {
        "Correct Answers": {
          "sort_ascending": false,
          "description": "Total number of correct answers"
        }
      }
    }

  - id: 2
    schema: {
      "labels": ["Average Response Time"],
      "default_order_by": "Average Response Time",
      "metadata": {
        "Average Response Time": {
          "sort_ascending": true,
          "description": "Average time taken to answer a question"
        }
      }
    }

challenge_phases:
  - id: 1
    name: QA Phase
    description: templates/challenge_phase_1_description.html
    leaderboard_public: true
    is_public: true
    challenge: 1
    is_active: true
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: false
    is_submission_public: true
    start_date: 2025-10-01 00:00:00
    end_date: 2026-01-31 23:59:59
    test_annotation_file: annotations/test_annotations_devsplit.json
    codename: qa
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: true
      - name: method_description
        is_visible: true
    submission_meta_attributes:
      - name: System Type
        description: Choose system type
        type: radio
        options: ["Rule-Based", "ML-Based"]
      - name: Open Source
        description: Is it open source?
        type: boolean
        required: false
    is_restricted_to_select_one_submission: false
    is_partial_submission_evaluation_enabled: false
    allowed_submission_file_types: ".json, .zip"

dataset_splits:
  - id: 1
    name: Accuracy Split
    codename: accuracy_split
  - id: 2
    name: Speed Split
    codename: speed_split

challenge_phase_splits:
  - challenge_phase_id: 1
    leaderboard_id: 1
    dataset_split_id: 1
    visibility: 1
    leaderboard_decimal_precision: 0
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: false

  - challenge_phase_id: 1
    leaderboard_id: 2
    dataset_split_id: 2
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: false
```

## Example 3: One Challenge, Two Phases, One Leaderboard, Two Phase Splits

example_3_config.yaml:

```yaml
title: "Object Detection Challenge"
short_description: "Detect objects in images."
description: "templates/description.html"
evaluation_details: "templates/evaluation_details.html"
terms_and_conditions: "templates/terms_and_conditions.html"
image: "logo.jpg"
submission_guidelines: "templates/submission_guidelines.html"
leaderboard_description: "Leaderboard evaluates detection performance using correct, missed, and combined scores."
evaluation_script: "evaluation_script.zip"
remote_evaluation: false
start_date: "2025-08-01 00:00:00"
end_date: "2026-01-01 23:59:59"
published: false
tags:
  - object-detection
  - computer-vision

leaderboard:
  - id: 1
    schema: {
      "labels": ["Correct Detections", "Missed Detections", "Overall Score"],
      "default_order_by": "Overall Score",
      "metadata": {
        "Correct Detections": {
          "sort_ascending": false,
          "description": "Number of correct object predictions"
        },
        "Missed Detections": {
          "sort_ascending": true,
          "description": "Number of objects the model failed to detect"
        },
        "Overall Score": {
          "sort_ascending": false,
          "description": "Combined score of accuracy and completeness"
        }
      }
    }

challenge_phases:
  - id: 1
    name: Dev Phase
    description: templates/challenge_phase_1_description.html
    leaderboard_public: true
    is_public: true
    challenge: 1
    is_active: true
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: false
    is_submission_public: true
    start_date: 2025-08-01 00:00:00
    end_date: 2025-10-15 23:59:59
    test_annotation_file: annotations/test_annotations_devsplit.json
    codename: dev
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: true
      - name: method_description
        is_visible: true
    submission_meta_attributes:
      - name: framework
        description: Framework used
        type: radio
        options: ["PyTorch", "TensorFlow", "Other"]
        required: false
      - name: open_source
        description: Is your code open source?
        type: boolean
        required: false
    is_restricted_to_select_one_submission: false
    is_partial_submission_evaluation_enabled: false
    allowed_submission_file_types: ".json, .zip"

  - id: 2
    name: Test Phase
    description: templates/challenge_phase_2_description.html
    leaderboard_public: true
    is_public: true
    challenge: 1
    is_active: false
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: false
    is_submission_public: true
    start_date: 2025-10-16 00:00:00
    end_date: 2026-01-01 23:59:59
    test_annotation_file: annotations/test_annotations_testsplit.json
    codename: test
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: true
      - name: method_description
        is_visible: true
    submission_meta_attributes:
      - name: framework
        description: Framework used
        type: radio
        options: ["PyTorch", "TensorFlow", "Other"]
        required: false
      - name: open_source
        description: Is your code open source?
        type: boolean
        required: false
    is_restricted_to_select_one_submission: false
    is_partial_submission_evaluation_enabled: false
    allowed_submission_file_types: ".json, .zip"

dataset_splits:
  - id: 1
    name: Dev Split
    codename: dev_split
  - id: 2
    name: Test Split
    codename: test_split

challenge_phase_splits:
  - challenge_phase_id: 1
    leaderboard_id: 1
    dataset_split_id: 1
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: true

  - challenge_phase_id: 2
    leaderboard_id: 1
    dataset_split_id: 2
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: true
```

## Example 4: One Challenge, Three Phases, Two Leaderboards, Four Phase Splits

example_4_config.yaml:

```yaml
title: "Multi-Stage NLP Challenge"
short_description: "NLP challenge with public/private testing."
description: "templates/description.html"
evaluation_details: "templates/evaluation_details.html"
terms_and_conditions: "templates/terms_and_conditions.html"
image: "logo.jpg"
submission_guidelines: "templates/submission_guidelines.html"
leaderboard_description: "Leaderboard evaluates both match accuracy and mismatch rate across multiple stages."
evaluation_script: "evaluation_script.zip"
remote_evaluation: false
start_date: "2025-09-01 00:00:00"
end_date: "2026-03-01 23:59:59"
published: false
tags: 
  - nlp
  - machine-learning

leaderboard:
  - id: 1
    schema: {
      "labels": ["Match Accuracy"],
      "default_order_by": "Match Accuracy",
      "metadata": {
        "Match Accuracy": {
          "sort_ascending": false,
          "description": "How accurately the model predicts matched pairs"
        }
      }
    }

  - id: 2
    schema: {
      "labels": ["Mismatch Rate"],
      "default_order_by": "Mismatch Rate",
      "metadata": {
        "Mismatch Rate": {
          "sort_ascending": true,
          "description": "How often the model incorrectly identifies non-matches"
        }
      }
    }

challenge_phases:
  - id: 1
    name: Dev Phase
    description: templates/challenge_phase_1_description.html
    leaderboard_public: true
    is_public: true
    challenge: 1
    is_active: true
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: false
    is_submission_public: true
    start_date: 2025-09-01 00:00:00
    end_date: 2025-10-15 23:59:59
    test_annotation_file: annotations/test_annotations_devsplit.json
    codename: dev
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: true
      - name: method_description
        is_visible: true
    submission_meta_attributes:
      - name: pretraining
        description: Was the model pretrained?
        type: radio
        options: ["Yes", "No"]
        required: false
      - name: public_code
        description: Is your code publicly available?
        type: boolean
        required: false
    is_restricted_to_select_one_submission: false
    is_partial_submission_evaluation_enabled: false
    allowed_submission_file_types: ".json, .zip"

  - id: 2
    name: Public Test
    description: templates/challenge_phase_2_description.html
    leaderboard_public: true
    is_public: true
    challenge: 1
    is_active: false
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: false
    is_submission_public: true
    start_date: 2025-10-16 00:00:00
    end_date: 2025-12-01 23:59:59
    test_annotation_file: annotations/test_annotations_public_split.json
    codename: test-public
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: true
      - name: method_description
        is_visible: true
    submission_meta_attributes:
      - name: pretraining
        description: Was the model pretrained?
        type: radio
        options: ["Yes", "No"]
        required: false
      - name: public_code
        description: Is your code publicly available?
        type: boolean
        required: false
    is_restricted_to_select_one_submission: false
    is_partial_submission_evaluation_enabled: false
    allowed_submission_file_types: ".json, .zip"

  - id: 3
    name: Private Test
    description: templates/challenge_phase_3_description.html
    leaderboard_public: true
    is_public: false
    challenge: 1
    is_active: false
    max_concurrent_submissions_allowed: 3
    allowed_email_ids: []
    disable_logs: false
    is_submission_public: true
    start_date: 2025-12-02 00:00:00
    end_date: 2026-03-01 23:59:59
    test_annotation_file: annotations/test_annotations_private_split.json
    codename: test-private
    max_submissions_per_day: 5
    max_submissions_per_month: 50
    max_submissions: 100
    default_submission_meta_attributes:
      - name: method_name
        is_visible: true
      - name: method_description
        is_visible: true
    submission_meta_attributes:
      - name: pretraining
        description: Was the model pretrained?
        type: radio
        options: ["Yes", "No"]
        required: false
      - name: public_code
        description: Is your code publicly available?
        type: boolean
        required: false
    is_restricted_to_select_one_submission: false
    is_partial_submission_evaluation_enabled: false
    allowed_submission_file_types: ".json, .zip"

dataset_splits:
  - id: 1
    name: Dev Split-1
    codename: dev_split
  - id: 2
    name: Public Test
    codename: test_pub_split
  - id: 3
    name: Private Test
    codename: test_priv_split

challenge_phase_splits:
  - challenge_phase_id: 1
    leaderboard_id: 1
    dataset_split_id: 1
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: true

  - challenge_phase_id: 1
    leaderboard_id: 2
    dataset_split_id: 1
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: true

  - challenge_phase_id: 2
    leaderboard_id: 2
    dataset_split_id: 2
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: true

  - challenge_phase_id: 3
    leaderboard_id: 2
    dataset_split_id: 3
    visibility: 1
    leaderboard_decimal_precision: 2
    is_leaderboard_order_descending: true
    show_execution_time: true
    show_leaderboard_by_latest_submission: true
```

