import requests
import base64
import logging

logger = logging.getLogger(__name__)

URLS = {"contents": "/repos/{}/contents/{}", "repos": "/repos/{}"}


class GithubInterface:
    def __init__(self, GITHUB_REPOSITORY, GITHUB_BRANCH, GITHUB_AUTH_TOKEN):
        self.GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN
        self.GITHUB_REPOSITORY = GITHUB_REPOSITORY
        self.BRANCH = GITHUB_BRANCH
        self.COMMIT_PREFIX = "evalai_bot: Update {}"
    
    def _serialize_field_value(self, field, value):
        """
        Serialize field values appropriately, handling datetime fields to preserve naive format
        """
        if value is None:
            return None
        
        # Handle datetime fields to preserve naive format without timezone info
        if field in ['start_date', 'end_date'] and hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        return value
    


    def get_request_headers(self):
        headers = {"Authorization": "token {}".format(self.GITHUB_AUTH_TOKEN)}
        return headers

    def make_request(self, url, method, params={}, data={}):
        url = self.get_github_url(url)
        headers = self.get_request_headers()
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "EvalAI is not able to establish connection with github {}".format(
                    response.json()
                )
            )
            return None
        return response.json()

    def get_github_url(self, url):
        base_url = "https://api.github.com"
        url = "{0}{1}".format(base_url, url)
        return url

    def get_content_from_path(self, path):
        """
        Gets the file content, information in json format in the repository at particular path
        Ref: https://docs.github.com/en/rest/reference/repos#contents
        """
        url = URLS.get("contents").format(self.GITHUB_REPOSITORY, path)
        params = {"ref": self.BRANCH}
        response = self.make_request(url, "GET", params)
        
        # If branch doesn't exist, try to create it or use default branch
        if response is None or (isinstance(response, dict) and response.get('message') == 'No commit found for the ref ' + self.BRANCH):
            logger.warning(f"Branch '{self.BRANCH}' not found, trying to create it or use default branch")
            # Try to get content from default branch (usually 'main' or 'master')
            for default_branch in ['main', 'master']:
                if default_branch != self.BRANCH:
                    logger.info(f"Trying default branch '{default_branch}'")
                    params = {"ref": default_branch}
                    response = self.make_request(url, "GET", params)
                    if response and not (isinstance(response, dict) and 'No commit found' in response.get('message', '')):
                        logger.info(f"Found content in default branch '{default_branch}'")
                        break
        
        return response

    def get_data_from_path(self, path):
        """
        Gets the file data in string format in the repository at particular path
        Calls get_content_from_path and encode the base64 content
        """
        content_response = self.get_content_from_path(path)
        string_data = None
        if content_response and content_response.get("content"):
            string_data = base64.b64decode(content_response["content"]).decode(
                "utf-8"
            )
        return string_data

    def update_content_from_path(self, path, content):
        """
        Updates the file content, creates a commit in the repository at particular path
        Ref: https://docs.github.com/en/rest/reference/repos#create-or-update-file-contents
        """
        url = URLS.get("contents").format(self.GITHUB_REPOSITORY, path)
        
        # Get existing content to get SHA (required for updates)
        existing_content = self.get_content_from_path(path)
        
        if existing_content and existing_content.get("sha"):
            # File exists, update it
            data = {
                "message": self.COMMIT_PREFIX.format(path),
                "branch": self.BRANCH,
                "sha": existing_content.get("sha"),
                "content": content,
            }
        else:
            # File doesn't exist, create it
            data = {
                "message": self.COMMIT_PREFIX.format(path),
                "branch": self.BRANCH,
                "content": content,
            }
        
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_data_from_path(self, path, data):
        """
        Updates the file data to the data(string) provided, at particular path
        Call update_content_from_path with decoded base64 content
        """
        content = base64.b64encode(bytes(data, "utf-8")).decode("utf-8")
        return self.update_content_from_path(path, content)

    def is_repository(self):
        url = URLS.get("repos").format(self.GITHUB_REPOSITORY)
        repo_response = self.make_request(url, "GET")
        return True if repo_response else False

    def update_challenge_config(self, challenge):
        """
        Update challenge configuration in GitHub repository
        Preserves existing structure and custom configuration while updating only EvalAI-managed fields
        """
        try:
            import yaml
            from collections import OrderedDict
            from challenges.github_sync_config import challenge_non_file_fields, challenge_file_fields
            
            # Get existing challenge config to preserve structure and custom fields
            existing_config = self.get_data_from_path("challenge_config.yaml")
            if existing_config:
                try:
                    config_data = yaml.safe_load(existing_config)
                    if not isinstance(config_data, dict):
                        config_data = {}
                except yaml.YAMLError:
                    logger.warning("Existing challenge_config.yaml is not valid YAML, starting fresh")
                    config_data = {}
            else:
                config_data = {}
            
            # Create ordered config with exact field order as specified
            ordered_config = OrderedDict()
            
            # Pre-extract all field values once to avoid multiple hasattr/getattr calls
            field_values = {}
            challenge_fields = ['title', 'short_description', 'description', 'evaluation_details', 'terms_and_conditions', 'image', 'submission_guidelines', 'leaderboard_description', 'evaluation_script', 'remote_evaluation', 'start_date', 'end_date', 'published', 'tags']
            
            for field in challenge_fields:
                if field in config_data:
                    field_values[field] = config_data[field]
                elif hasattr(challenge, field):
                    field_values[field] = getattr(challenge, field)
            
            # Add fields in the exact order specified with efficient processing
            for field in challenge_fields:
                if field in field_values:
                    value = field_values[field]
                    if value is None:
                        continue
                        
                    # Process field value based on type
                    if field in ['start_date', 'end_date'] and hasattr(value, 'strftime'):
                        ordered_config[field] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif field in ['description', 'evaluation_details', 'terms_and_conditions', 'submission_guidelines']:
                        # Extract content from HTML fields
                        if hasattr(value, 'read'):
                            try:
                                value.seek(0)
                                content = value.read().decode('utf-8')
                                ordered_config[field] = content
                            except:
                                ordered_config[field] = str(value)
                        else:
                            ordered_config[field] = str(value)
                    elif field in ['image', 'evaluation_script']:
                        # Handle file fields - extract filename/path
                        if hasattr(value, 'name'):
                            ordered_config[field] = value.name
                        else:
                            ordered_config[field] = str(value)
                    else:
                        # Handle other field types
                        if hasattr(value, 'pk'):  # Django model instance
                            ordered_config[field] = value.pk
                        elif hasattr(value, 'id'):  # Django model instance
                            ordered_config[field] = value.id
                        elif isinstance(value, (list, tuple)):  # Handle lists/tuples
                            clean_list = []
                            for item in value:
                                if hasattr(item, 'pk'):
                                    clean_list.append(item.pk)
                                elif hasattr(item, 'id'):
                                    clean_list.append(item.id)
                                else:
                                    clean_list.append(item)
                            ordered_config[field] = clean_list
                        else:
                            ordered_config[field] = value
            
            # Sync additional sections in the correct order
            try:
                # Sync leaderboard information if available
                if hasattr(challenge, 'leaderboard') and challenge.leaderboard:
                    ordered_config['leaderboard'] = challenge.leaderboard
                elif 'leaderboard' in config_data:
                    ordered_config['leaderboard'] = config_data['leaderboard']
                
                # Sync challenge phases if available
                if hasattr(challenge, 'challenge_phases') and challenge.challenge_phases.exists():
                    challenge_phases = []
                    for phase in challenge.challenge_phases.all():
                        phase_data = OrderedDict()
                        # Add phase fields in the exact order specified
                        phase_fields = ['id', 'name', 'description', 'leaderboard_public', 'is_public', 'challenge', 'is_active', 'max_concurrent_submissions_allowed', 'allowed_email_ids', 'disable_logs', 'is_submission_public', 'start_date', 'end_date', 'test_annotation_file', 'codename', 'max_submissions_per_day', 'max_submissions_per_month', 'max_submissions', 'default_submission_meta_attributes', 'submission_meta_attributes', 'is_restricted_to_select_one_submission', 'is_partial_submission_evaluation_enabled', 'allowed_submission_file_types']
                        
                        for field in phase_fields:
                            if hasattr(phase, field):
                                value = getattr(phase, field)
                                if field in ['start_date', 'end_date'] and hasattr(value, 'strftime'):
                                    phase_data[field] = value.strftime('%Y-%m-%d %H:%M:%S')
                                elif field == 'description' and value:
                                    # Extract the actual content from HTML fields
                                    if hasattr(value, 'read'):
                                        # It's a file-like object, read the content
                                        try:
                                            value.seek(0)
                                            content = value.read().decode('utf-8')
                                            phase_data[field] = content
                                        except:
                                            phase_data[field] = str(value)
                                    else:
                                        phase_data[field] = str(value)
                                elif value is not None:
                                    # Handle Django model fields and related objects
                                    if hasattr(value, 'pk'):  # Django model instance
                                        phase_data[field] = value.pk
                                    elif hasattr(value, 'id'):  # Django model instance
                                        phase_data[field] = value.id
                                    elif isinstance(value, (list, tuple)):  # Handle lists/tuples
                                        # Convert to list of simple values
                                        clean_list = []
                                        for item in value:
                                            if hasattr(item, 'pk'):
                                                clean_list.append(item.pk)
                                            elif hasattr(item, 'id'):
                                                clean_list.append(item.id)
                                            else:
                                                clean_list.append(item)
                                        phase_data[field] = clean_list
                                    else:
                                        phase_data[field] = value
                        
                        challenge_phases.append(phase_data)
                    ordered_config['challenge_phases'] = challenge_phases
                elif 'challenge_phases' in config_data:
                    ordered_config['challenge_phases'] = config_data['challenge_phases']
                
                # Sync dataset splits if available
                if hasattr(challenge, 'dataset_splits') and challenge.dataset_splits.exists():
                    dataset_splits = []
                    for split in challenge.dataset_splits.all():
                        split_data = OrderedDict([
                            ('id', split.id),
                            ('name', split.name),
                            ('codename', split.codename),
                        ])
                        dataset_splits.append(split_data)
                    ordered_config['dataset_splits'] = dataset_splits
                elif 'dataset_splits' in config_data:
                    ordered_config['dataset_splits'] = config_data['dataset_splits']
                
                # Sync challenge phase splits if available
                if hasattr(challenge, 'challenge_phases') and challenge.challenge_phases.exists():
                    phase_splits = []
                    for phase in challenge.challenge_phases.all():
                        if hasattr(phase, 'challenge_phase_splits') and phase.challenge_phase_splits.exists():
                            for split in phase.challenge_phase_splits.all():
                                split_data = OrderedDict([
                                    ('challenge_phase_id', split.challenge_phase.id),
                                    ('leaderboard_id', split.leaderboard.id if split.leaderboard else None),
                                    ('dataset_split_id', split.dataset_split.id if split.dataset_split else None),
                                    ('visibility', split.visibility),
                                    ('leaderboard_decimal_precision', split.leaderboard_decimal_precision),
                                    ('is_leaderboard_order_descending', split.is_leaderboard_order_descending),
                                    ('show_execution_time', split.show_execution_time),
                                    ('show_leaderboard_by_latest_submission', split.show_leaderboard_by_latest_submission),
                                ])
                                phase_splits.append(split_data)
                    ordered_config['challenge_phase_splits'] = phase_splits
                elif 'challenge_phase_splits' in config_data:
                    ordered_config['challenge_phase_splits'] = config_data['challenge_phase_splits']
                    
            except Exception as e:
                logger.warning(f"Error syncing additional sections: {str(e)}")
                # Continue without failing the entire sync
            
            # Use the ordered config for YAML generation
            config_data = ordered_config
            
            # Convert to YAML with custom representer to handle OrderedDict properly
            def represent_ordereddict(dumper, data):
                return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
            
            yaml.add_representer(OrderedDict, represent_ordereddict)
            yaml_content = yaml.dump(config_data, default_flow_style=False, allow_unicode=True)
            
            # Add the documentation header comment
            header_comment = "# If you are not sure what all these fields mean, please refer our documentation here:\n# https://evalai.readthedocs.io/en/latest/configuration.html\n"
            yaml_content = header_comment + yaml_content
            
            # Update the file in GitHub
            success = self.update_data_from_path("challenge_config.yaml", yaml_content)
            
            if success:
                logger.info(f"Successfully updated challenge config for challenge {challenge.id} while preserving existing structure")
                return True
            else:
                logger.error(f"Failed to update challenge config for challenge {challenge.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating challenge config: {str(e)}")
            return False

    def update_challenge_phase_config(self, challenge_phase):
        """
        Update challenge phase configuration in GitHub repository
        Preserves existing structure and custom configuration while updating only phase information
        """
        try:
            import yaml
            from challenges.github_sync_config import challenge_phase_non_file_fields, challenge_phase_file_fields
            
            # Get existing challenge config to preserve structure and custom fields
            existing_config = self.get_data_from_path("challenge_config.yaml")
            if existing_config:
                try:
                    config_data = yaml.safe_load(existing_config)
                    if not isinstance(config_data, dict):
                        config_data = {}
                except yaml.YAMLError:
                    logger.warning("Existing challenge_config.yaml is not valid YAML, starting fresh")
                    config_data = {}
            else:
                config_data = {}
            
            # Initialize challenge_phases section if it doesn't exist
            if 'challenge_phases' not in config_data:
                config_data['challenge_phases'] = []
            
            # Find existing phase or create new one
            phase_data = {}
            for field in challenge_phase_non_file_fields:
                if hasattr(challenge_phase, field):
                    value = getattr(challenge_phase, field)
                    serialized_value = self._serialize_field_value(field, value)
                    if serialized_value is not None:
                        phase_data[field] = serialized_value
            
            # Add file fields
            for field in challenge_phase_file_fields:
                if hasattr(challenge_phase, field):
                    value = getattr(challenge_phase, field)
                    if value:
                        phase_data[field] = str(value)
            
            # Update or add phase
            phase_found = False
            for i, phase in enumerate(config_data['challenge_phases']):
                if phase.get('codename') == challenge_phase.codename:
                    config_data['challenge_phases'][i] = phase_data
                    phase_found = True
                    break
            
            if not phase_found:
                config_data['challenge_phases'].append(phase_data)
            
            # Convert back to YAML
            yaml_content = yaml.dump(config_data, default_flow_style=False, allow_unicode=True)
            
            # Update the file in GitHub
            success = self.update_data_from_path("challenge_config.yaml", yaml_content)
            
            if success:
                logger.info(f"Successfully updated challenge phase config for phase {challenge_phase.id} while preserving existing structure")
                return True
            else:
                logger.error(f"Failed to update challenge phase config for phase {challenge_phase.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating challenge phase config: {str(e)}")
            return False