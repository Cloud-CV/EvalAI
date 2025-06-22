submission = """
{
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
        {
            "challenge_phase": 7,
            "created_by": 4,
            "execution_time": "None",
            "id": 9,
            "input_file": "http://testserver/media/submission_files/submission_9/2224fb89-6828-47f4-\
            b170-1279290ad900.json",
            "is_public": false,
            "method_description": null,
            "method_name": null,
            "participant_team": 3,
            "participant_team_name": "Host_83644_Team",
            "project_url": null,
            "publication_url": null,
            "status": "submitted",
            "stderr_file": null,
            "stdout_file": null,
            "submission_result_file": null,
            "submitted_at": "2018-06-03T09:24:09.866590Z",
            "when_made_public": null
        },
        {
            "challenge_phase": 7,
            "created_by": 4,
            "execution_time": 0.008033,
            "id": 8,
            "input_file": "http://testserver/media/submission_files/submission_8/34a4102c-fa01-\
            470b-b24b-d724ad0c8238.txt",
            "is_public": false,
            "method_description": null,
            "method_name": null,
            "participant_team": 3,
            "participant_team_name": "Host_83644_Team",
            "project_url": null,
            "publication_url": null,
            "status": "failed",
            "stderr_file": "http://testserver/media/submission_files/submission_8/dedc8234-8ae9-4d8c-\
            a3b2-8aaa7bf6bf9a.txt",
            "stdout_file": "http://testserver/media/submission_files/submission_8/f6587e1a-632e-4be1-93bd-\
            ae3c23bd5e7d.txt",
            "submission_result_file": "http://testserver/media/submission_files/submission_8/2eebf2ab-6f6e-485f-\
            ab54-aea3cbbeb06b.json",
            "submitted_at": "2018-06-05T18:18:08.996609Z",
            "when_made_public": null
        },
        {
            "challenge_phase": 7,
            "created_by": 4,
            "execution_time": 0.020234,
            "id": 7,
            "input_file": "http://testserver/media/submission_files/submission_7/50b2ef72-fc70-\
            4252-8b35-6d0b9d4e9813.txt",
            "is_public": false,
            "method_description": null,
            "method_name": null,
            "participant_team": 3,
            "participant_team_name": "Host_83644_Team",
            "project_url": null,
            "publication_url": null,
            "status": "failed",
            "stderr_file": "http://testserver/media/submission_files/submission_7/b60f7eeb-d74c-4d07-\
            a848-2f5cdf5a7e44.txt",
            "stdout_file": "http://testserver/media/submission_files/submission_7/48c58bba-a459-4e16-\
            ba2f-1b236f9ef0f0.txt",
            "submission_result_file": "http://testserver/media/submission_files/submission_7/ddb15eda-\
            fc37-4b0d-b9e8-cb83ae261f71.json",
            "submitted_at": "2018-06-07T18:18:07.301134Z",
            "when_made_public": null
        },
        {
            "challenge_phase": 7,
            "created_by": 4,
            "execution_time": 0.012286,
            "id": 6,
            "input_file": "http://testserver/media/submission_files/submission_6/1826cd23-2a29-0e8d3069d916.txt",
            "is_public": false,
            "method_description": null,
            "method_name": null,
            "participant_team": 3,
            "participant_team_name": "Host_83644_Team",
            "project_url": null,
            "publication_url": null,
            "status": "failed",
            "stderr_file": "http://testserver/media/submission_files/submission_6/932886df-0472-4630-\
            b810-0c6128b76e79.txt",
            "stdout_file": "http://testserver/media/submission_files/submission_6/3ff4e52f-40db-4e6f-\
            a352-d41e15348a20.txt",
            "submission_result_file": "http://testserver/media/submission_files/submission_6/b0f44621-\
            0560-4baa-a758-9b4d9e328e39.json",
            "submitted_at": "2018-06-09T18:17:08.739749Z",
            "when_made_public": null
        }
    ]
}"""


submission_result = """
{
    "challenge_phase": 7,
    "created_by": 4,
    "execution_time": "None",
    "id": 9,
    "input_file": "http://testserver/media/submission_files/submission_9/2224fb89-6828-\
    47f4-b170-1279290ad900.json",
    "is_public": false,
    "method_description": null,
    "method_name": null,
    "participant_team": 3,
    "participant_team_name": "Host_83644_Team",
    "project_url": null,
    "publication_url": null,
    "status": "submitted",
    "stderr_file": null,
    "stdout_file": null,
    "submission_result_file": "http://testserver/media/submission_files/submission_9/result.json",
    "submitted_at": "2018-06-08T09:24:09.866590Z",
    "when_made_public": null
}
"""

aws_credentials = """
{
    "success": {
        "federated_user": {
            "Credentials": {
                "AccessKeyId": "ABCDEFGHIJKLMNOPQRTUVWXYZ",
                "SecretAccessKey": "NMgBB75gfVBCDEFGHIJK8g00qVyyzQW+4XjJGQALMNOPQRSTUV",
                "SessionToken": "FQoGZX.....",
                "Expiration": "7845124587452165"
            },
            "FederatedUser": {
                "FederatedUserId": "1234567890:test-user",
                "Arn": "arn:aws:sts::1234567890:federated-user/test-user"
            },
            "PackedPolicySize": 28,
            "ResponseMetadata": {
                "RequestId": "fb47f78b-2a92-11e9-84b9-33527429b818",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amzn-requestid": "fb47f78b-2a92-11e9-84b9-33527429b818",
                    "content-type": "text/xml",
                    "content-length": "1245",
                    "date": "Thu, 07 Feb 2019 04:43:57 GMT"
                },
                "RetryAttempts": 0
            }
        },
        "docker_repository_uri": "aws_account_id.dkr.ecr.us-east-1.amazonaws.com/evalai-test-repository2"
    }
}
"""

submission_result_file = """
[{"Total": 60, "Metric1": 61, "Metric2": 62, "Metric3": 63}]
"""
