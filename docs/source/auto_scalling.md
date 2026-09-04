## EC2 Workers Auto Scaling Script Documentation

### Overview

This script automates the scaling of EC2 instances based on the pending submissions in the EvalAI challenges. It utilizes AWS services to start or stop instances dynamically, ensuring that resources are efficiently utilized. The script is designed to run as a cron job, checking periodically for the need to adjust the number of active EC2 instances.

### Key Features

- **Dynamic Scaling:** Automatically starts or stops EC2 instances based on the number of pending submissions.
- **Integration with EvalAI:** Retrieves challenge details and submission metrics from EvalAI to make scaling decisions.
- **Environment Configuration:** Uses environment variables for configuration, allowing for flexibility across different deployment environments.
- **AWS Integration:** Leverages AWS SDK for Python (Boto3) to manage EC2 instances.

### Requirements

- Python 3.x
- Boto3
- Pytz
- A valid AWS account with access to EC2 services.
- Access tokens and credentials for EvalAI API.

### Setup

1. **Install Dependencies:**
   Ensure Python 3.x is installed on your system. Install required Python packages using pip:
   ```
   pip install boto3 pytz
   ```
2. **Configure Environment Variables:**
   Set the following environment variables:
   - `ENV`: The environment the script is running in (e.g., "dev" for development).
   - `API_HOST_URL`: The EvalAI API endpoint URL.
   - `AUTH_TOKEN`: The authentication token for accessing EvalAI API.

3. **AWS Credentials:**
   Configure your AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION) to allow Boto3 to interact with AWS services.

### Usage

Execute the script from the command line:

```
python auto_scaling_script.py
```

The script will automatically manage the scaling of EC2 instances based on the pending submissions for challenges that use EC2 workers.

### Limitations and Liability Disclaimer

This auto-scaling script is provided "as is," with no guarantees of completeness, accuracy, or timeliness, and without warranties of any kind, express or implied. The creators of the script are not liable for any damages, loss of profit, or any other loss incurred as a result of the direct or indirect use of this script.

#### Important Notes:

- **AWS Usage Monitoring:** Users are advised to regularly monitor their AWS usage to avoid unexpected charges. The script dynamically scales EC2 instances which could lead to increased AWS costs.
- **Scaling Failures:** In scenarios where auto-scaling fails to adjust resources appropriately, users should manually check their AWS usage and scale down resources if necessary.
- **Support:** For assistance or to report issues with the script, users should contact the script maintainers.

### Function Descriptions

#### `get_boto3_client(resource, aws_keys)`

This function initializes and returns a Boto3 client for interfacing with AWS services specified by the `resource` parameter, using credentials provided in `aws_keys`. It simplifies the process of connecting to AWS with the necessary credentials for region, access key ID, and secret access key, facilitating operations such as starting or stopping EC2 instances.

#### `get_pending_submission_count(challenge_metrics)`

Calculates the total number of pending submissions for a given challenge by summing up the submissions in various statuses like "running", "submitted", "queued", and "resuming". This function is critical for determining the workload associated with a challenge and deciding whether additional computational resources are needed or excess resources can be scaled down.

#### `stop_instance(challenge, evalai_interface)`

Attempts to stop a running EC2 instance for a specific challenge. It checks if the instance is in the "running" state and, if so, sends a request through `evalai_interface` to stop the instance. This function is essential for resource management, ensuring that instances are not running unnecessarily, thus saving on costs.

#### `start_instance(challenge, evalai_interface)`

Checks whether the EC2 instance associated with a specific challenge is stopped; if it is, the function initiates a request to start the instance. This is a crucial component of the auto-scaling mechanism, allowing the script to bring computational resources online as needed to handle challenge submissions.

#### `start_or_stop_workers(challenge, challenge_metrics, evalai_interface)`

Determines whether to start or stop EC2 instances based on the number of pending submissions and the challenge's end date. It integrates the functionality of both `start_instance` and `stop_instance` functions, making a decision based on the current needs: stopping instances if there are no pending submissions or if the challenge has ended, and starting instances if there are submissions that need processing.

#### `start_or_stop_workers_for_challenges(response, metrics, evalai_interface)`

Iterates over a list of challenges, deciding for each whether to start or stop worker instances based on their current status and workload. This function extends the auto-scaling logic to multiple challenges, ensuring that resources are allocated efficiently across all active challenges.

#### `create_evalai_interface(auth_token, evalai_endpoint)`

Initializes an interface to EvalAI by creating an instance of the `EvalAI_Interface` class, using the provided `auth_token` and `evalai_endpoint`. This interface is used throughout the script to interact with EvalAI for operations such as fetching challenge details, submission metrics, and managing EC2 instances.

#### `start_job()`

Serves as the main entry point for the auto-scaling script, orchestrating the overall process. It initializes the EvalAI interface, fetches challenges and their metrics, and iteratively processes each challenge to manage EC2 workers appropriately. The function also handles pagination to ensure all challenges are considered.


## EKS Nodegroup Auto Scaling Script Documentation

### Overview

This script is designed to automate the scaling of Amazon EKS (Elastic Kubernetes Service) nodegroups based on the number of pending submissions in EvalAI challenges. It adjusts the size of the nodegroups dynamically, ensuring efficient utilization of resources. The script is particularly tailored for challenges hosted on EvalAI that require computational resources managed by Kubernetes on AWS EKS.

### Key Features

- **Dynamic Scaling:** Automatically adjusts the size of EKS nodegroups based on the workload from pending submissions.
- **Integration with EvalAI:** Utilizes EvalAI's interface to fetch challenge details and submission metrics for making informed scaling decisions.
- **Customizable Scaling Parameters:** Allows for the configuration of scale-up sizes and uses specific AWS credentials per challenge.
- **Automated Resource Management:** Helps in reducing costs and optimizing resource utilization by scaling down resources when not needed.

### Requirements

- Python 3.x
- Boto3 and Pytz libraries.
- Access to AWS with permissions to manage EKS nodegroups.
- EvalAI API access for fetching challenge and submission data.

### Setup Instructions

1. **Install Dependencies:** Make sure Python 3.x is installed. Use pip to install Boto3 and Pytz if not already installed.
   ```
   pip install boto3 pytz
   ```
2. **Configure Environment Variables:** Set necessary environment variables including AWS credentials (specific to EKS), EvalAI authentication token, and API host URL.
3. **JSON Configuration for Challenges:** Ensure the `prod_eks_auth_tokens.json` file is correctly configured with challenge IDs, AWS keys, and any other relevant parameters for each challenge.

### How It Works

1. **Initialization:** The script initializes by loading configuration from environment variables and a JSON file containing details about which challenges to scale, their AWS credentials, and desired scaling parameters.
2. **Challenge Processing:** For each challenge specified, the script checks for pending submissions and decides whether to scale up or down the nodegroup based on predefined rules.
3. **Scaling Decision:** If there are pending submissions and the current nodegroup size is less than the desired size, it scales up. If there are no pending submissions or the challenge has ended, it scales down the nodegroup.
4. **EKS and AWS Integration:** Utilizes Boto3 to interact with AWS EKS for managing nodegroup configurations based on the scaling decisions made.

### Function Descriptions

 #### `create_evalai_interface(auth_token)`
 Initializes communication with the EvalAI API using the provided authentication token.
 #### `get_boto3_client(resource, aws_keys)`:
 Establishes a Boto3 client for interacting with AWS services using specified credentials.
 #### `get_nodegroup_name(eks_client, cluster_name)`
Retrieves the name of the first nodegroup associated with a given EKS cluster.
 #### `get_eks_meta(challenge, evalai_interface, aws_keys)`
Fetches metadata for EKS including the client, cluster name, and nodegroup name, required for scaling operations.
 #### `get_scaling_config(eks_client, cluster_name, nodegroup_name)`
Gets the current scaling configuration of a specified EKS nodegroup.
 #### `start_eks_worker` & `stop_eks_worker(challenge, pending_submissions, evalai_interface, aws_keys, new_desired_size)` 
Commands to adjust the nodegroup size, either scaling up or down based on the number of pending submissions.
 #### `get_pending_submission_count_by_pk(metrics, challenge_pk)`
Calculates the total pending submissions for a challenge by its ID.
 #### `scale_up_or_down_workers(challenge, desired_size, evalai_interface, aws_keys)`
Main logic determining whether to scale up or down based on submissions and the current nodegroup size.
 #### `start_job()`
Entry point for the script to process each challenge and apply scaling as necessary.

### Limitations and Liability Disclaimer

This auto-scaling script is provided without warranty of any kind, express or implied. While it aims to efficiently manage AWS EKS nodegroups based on EvalAI challenge demands, users are advised to monitor their AWS usage closely to avoid unintended expenses. In case of unexpected behavior or failure of the script to properly scale resources, users should manually review their AWS configurations and adjust as necessary to maintain control over resource consumption and costs. For assistance or to report issues, users should contact the maintainers of this script.


## Worker Auto Scaling Script Documentation

### Overview

This auto-scaling script is designed to manage computational workers based on the workload of EvalAI challenges. It dynamically scales the number of workers up or down depending on the number of pending submissions for each challenge. By monitoring the status of submissions and the challenge end dates, the script ensures that resources are allocated efficiently, optimizing both performance and cost.

### Key Features

- **Dynamic Resource Management:** Automatically adjusts the number of workers based on real-time demand indicated by pending submissions.
- **Integration with EvalAI:** Leverages EvalAI's API to fetch current challenge metrics and statuses, enabling tailored scaling decisions.
- **Efficient Use of Resources:** Prevents unnecessary resource expenditure by stopping workers when they are not needed and starting workers when demand increases.
- **Environment-Specific Operation:** Customizable to operate differently based on the environment setting (development or production).

### Function Descriptions

#### `get_pending_submission_count(challenge_metrics)`

Calculates and returns the total number of pending submissions for a challenge. It aggregates submissions across several statuses, including "running", "submitted", "queued", and "resuming", to gauge the current workload.

#### `scale_down_workers(challenge, num_workers)`

Reduces the number of active workers for a challenge if there are more workers than needed (indicated by `num_workers`). It invokes the `stop_worker` function for the specified challenge if the current worker count is greater than zero, thereby conserving resources.

#### `scale_up_workers(challenge, num_workers)`

Increases the number of active workers for a challenge if there are no workers currently running but submissions are pending. It calls the `start_worker` function for the challenge, ensuring that there are sufficient resources to process submissions.

#### `scale_up_or_down_workers(challenge, challenge_metrics)`

Determines whether to scale up or down the number of workers for a challenge based on the number of pending submissions and the challenge's end date. This function serves as the decision-making hub, directing whether to invoke scaling up or down as needed.

#### `scale_up_or_down_workers_for_challenges(response, metrics)`

Iterates over a collection of challenges and applies the scaling logic to each, based on the environment setting. It ensures that all challenges fetched from EvalAI are evaluated and appropriately scaled.

#### `create_evalai_interface(auth_token, evalai_endpoint)`

Initializes an interface to interact with EvalAI, facilitating the retrieval of challenge information and submission metrics necessary for making scaling decisions.

#### `start_job()`

Serves as the entry point for the scaling script's execution, orchestrating the retrieval of challenge data from EvalAI and applying the auto-scaling logic across all challenges. It also handles pagination to ensure all challenges are processed.

### Important Notes

#### Limitations and Disclaimer

This script is provided "as-is" without any warranty. While it aims to efficiently manage resources by auto-scaling workers, users should monitor their resource usage and costs on AWS. There are scenarios where manual intervention may be necessary, especially if the auto-scaling script does not perform as expected or fails to scale resources appropriately.

#### AWS Usage Monitoring

Users are advised to regularly check their AWS usage to prevent unexpected charges. If auto-scaling does not scale down resources when demand decreases, users should manually reduce resource allocation to avoid unnecessary costs.

## Worker Auto Start/Stop Script Documentation

### Overview

This script is designed to manage the lifecycle of workers for challenges on EvalAI by automatically starting, stopping, or deleting workers based on the challenge's status and requirements. It uses the EvalAI API to fetch challenge details and applies logic to determine the necessary action for each worker associated with a challenge, such as stopping workers for ended or unapproved challenges or deleting workers under specific conditions.

### Key Features

- **Automated Worker Management:** Streamlines the process of starting, stopping, and deleting workers for EvalAI challenges.
- **Integration with EvalAI API:** Utilizes EvalAI's API endpoints to fetch challenge data and manage worker states.
- **Condition-Based Execution:** Performs actions based on the challenge's approval status, end date, and whether it is Docker-based.

### Function Descriptions

#### `execute_get_request(url)`

Sends a GET request to the specified URL, which is used to fetch data from EvalAI's API endpoints. It returns the response in JSON format.

#### `start_worker(challenge_id)`

Sends a PUT request to start a worker for a specific challenge identified by `challenge_id`. This function is designed to ensure that resources are available to process submissions for active challenges.

#### `stop_worker(challenge_id)`

Sends a PUT request to stop a worker for a specific challenge based on `challenge_id`. This action is taken to conserve resources for challenges that no longer require active workers.

#### `delete_worker(challenge_id)`

Sends a PUT request to delete a worker for a specific challenge, removing it entirely. This is typically done for challenges that are ended, unapproved, or otherwise inactive.

#### `get_challenges()`

Fetches a list of all challenges from EvalAI, including details necessary to determine whether workers should be started, stopped, or deleted.

#### `is_unapproved_challenge(workers, approved_by_admin, created_at)`

Determines whether a challenge is unapproved based on its worker status, admin approval, and creation date. This helps identify challenges that may not require active workers.

#### `stop_workers_for_challenges(response)`

Iterates over the challenges fetched from EvalAI and applies logic to stop or delete workers based on the challenge's status, end date, and Docker-based designation.

#### `start_job()`

Serves as the main function to initiate the worker management process. It fetches challenges and applies the stop/delete logic, including handling pagination for challenges listed across multiple pages.

### Important Notes

#### Limitations and Liability Disclaimer

This script is provided "as-is" without any warranty of its functionality or reliability. Users are advised to monitor their resource usage on EvalAI and AWS closely. In cases where the auto-scaling script fails or does not perform as expected, manual intervention may be necessary to prevent unnecessary resource usage and costs.

#### AWS Usage Monitoring

It is crucial for users to regularly check their AWS resource usage to manage costs effectively. If auto-scaling or auto-start/stop mechanisms fail, users should manually scale down or stop resources to avoid incurring unexpected expenses.


## Auto-Cancel Submissions Script Documentation

### Overview

This script is designed to automatically cancel submissions for EvalAI challenges that have been in "submitted", "running", or "resuming" status for more than a specified threshold of days. It aims to improve resource management and efficiency by identifying and canceling submissions that have stalled or are no longer active, ensuring resources are available for new and active submissions.

### Key Features

- **Automated Submission Management:** Identifies and cancels submissions that exceed the specified time threshold in their processing status.
- **Flexible Time Threshold:** Allows customization of the days threshold, with a default setting of 14 days, to accommodate different challenge requirements.
- **Comprehensive Status Check:** Considers submissions in "submitted", "running", and "resuming" statuses for potential cancellation.
- **Timezone Awareness:** Utilizes `pytz` for timezone-aware datetime operations, ensuring accurate time difference calculations.

### Function Descriptions

#### `get_submission_time(submission)`

Extracts and returns the submission time from a submission object. It prioritizes the "rerun_resumed_at" timestamp if available; otherwise, it uses the "submitted_at" timestamp. This function ensures accurate determination of how long a submission has been in its current status.

#### `auto_cancel_submissions(challenge_pk, days_threshold=14)`

Main function that iterates over submissions for a given challenge (identified by `challenge_pk`) and cancels those exceeding the `days_threshold`. It fetches submissions in relevant statuses, calculates how long each submission has been in its current status, and cancels submissions that have exceeded the threshold. This function encapsulates the script's core logic, leveraging `EvalAI_Interface` for interaction with the EvalAI API.

### Implementation Details

- **EvalAI API Integration:** The script uses `EvalAI_Interface` for API calls to fetch challenge submissions and update their status. This interface requires an authentication token (`AUTH_TOKEN`) and the EvalAI API server URL (`EVALAI_API_SERVER`) to be set as environment variables.
- **Datetime Handling:** Submission times are parsed and converted to timezone-aware datetime objects using `pytz`, ensuring accurate time difference calculations across different time zones.
- **Loop Through Challenges:** The script retrieves all challenges from EvalAI and runs the auto-cancel logic for each, making it suitable for batch processing across multiple challenges.

### Important Notes

#### Limitations and Liability Disclaimer

This script is provided "as-is" with no warranty for its functionality or effectiveness. Users are advised to monitor their EvalAI challenges and submissions closely. In scenarios where the script fails or does not perform as expected, manual intervention may be necessary to manage submissions and resources effectively.

#### Resource Usage Monitoring

Users should regularly check their resource usage associated with EvalAI challenges, especially if using external services like AWS or Azure, to avoid unintended expenses. Manual adjustments may be required if auto-cancellation fails to reduce resource consumption adequately.

#### Support and Contact
For support, feature requests, or contributions, users are encouraged to reach out through the project's GitHub repository or the provided contact information.For issues, questions, or assistance with the script, users should reach out to the support team or the script maintainers. Feedback and reports of problems are invaluable for improving the script and addressing user needs.





