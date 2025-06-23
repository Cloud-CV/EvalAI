# YAML Reference

An example of a complete `challenge_config.yaml `file of a sample challenge containing all the fields and subfields discussed till now:

```yaml
title: "Autonomous Driving Lane Detection Challenge"
short_description: "Detect lane boundaries from images in real-time."
description: "templates/description.html"
evaluation_details: "templates/evaluation_details.html"
terms_and_conditions: "templates/terms_and_conditions.html"
image: "images/logo/lane_detection_logo.png"
submission_guidelines: "templates/submission_guidelines.html"
leaderboard_description: "The leaderboard shows the evaluation results of your submissions based on accuracy and F1 score. The higher the score, the better your model performs."
evaluation_script: "evaluation_script/"
remote_evaluation: false
start_date: "2025-09-01 00:00:00"
end_date: "2025-12-01 23:59:59"
published: false
tags: 
  - autonomous-driving
  - lane-detection
  - computer-vision
  - real-time-processing
leaderboard:
  - id: 1
    schema: {
      "labels": ["Accuracy", "F1 Score", "Total"],
      "default_order_by": "Total",
      "metadata": {
        "Accuracy": {
          "sort_ascending": false,
          "description": "Overall accuracy of the model"
        },
        "F1 Score": {
          "sort_ascending": false,
          "description": "Weighted F1 score over all classes"
        },
        "Total": {
          "sort_ascending": false,
          "description": "Combined performance metric"
        }
      }
    }


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