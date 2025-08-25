import requests
import base64
import logging
import yaml

logger = logging.getLogger(__name__)

URLS = {"contents": "/repos/{}/contents/{}", "repos": "/repos/{}"}


class GithubInterface:
    def __init__(self, GITHUB_REPOSITORY, GITHUB_BRANCH, GITHUB_AUTH_TOKEN):
        self.GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN
        self.GITHUB_REPOSITORY = GITHUB_REPOSITORY
        self.BRANCH = GITHUB_BRANCH or "challenge"
        self.COMMIT_PREFIX = "evalai_bot: Update {}"

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
                "utf-8", errors="ignore"
            )
        return string_data

    def update_content_from_path(self, path, content, changed_field=None):
        """
        Updates the file content, creates a commit in the repository at particular path
        Ref: https://docs.github.com/en/rest/reference/repos#create-or-update-file-contents
        """
        url = URLS.get("contents").format(self.GITHUB_REPOSITORY, path)
        
        # Get existing content to get SHA (required for updates)
        existing_content = self.get_content_from_path(path)
        
        # Create specific commit message
        if changed_field:
            commit_message = f"evalai_bot: Update {path} - changed field: {changed_field}"
        else:
            commit_message = self.COMMIT_PREFIX.format(path)
        
        if existing_content and existing_content.get("sha"):
            # File exists, update it
            data = {
                "message": commit_message,
                "branch": self.BRANCH,
                "sha": existing_content.get("sha"),
                "content": content,
            }
        else:
            # File doesn't exist, create it
            data = {
                "message": commit_message,
                "branch": self.BRANCH,
                "content": content,
            }
        
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_data_from_path(self, path, data, changed_field=None):
        """
        Updates the file data to the data(string) provided, at particular path
        Call update_content_from_path with decoded base64 content
        """
        content = base64.b64encode(bytes(data, "utf-8")).decode("utf-8")
        return self.update_content_from_path(path, content, changed_field)

    def is_repository(self):
        url = URLS.get("repos").format(self.GITHUB_REPOSITORY)
        repo_response = self.make_request(url, "GET")
        return True if repo_response else False

    def _read_text_from_file_field(self, value):
        """Best-effort read of text from a Django FileField-like value."""
        if value is None:
            return None
        try:
            # Django FieldFile has open/read
            if hasattr(value, "open"):
                value.open("rb")
                data = value.read()
                value.close()
            elif hasattr(value, "read"):
                data = value.read()
            else:
                data = str(value)
            if isinstance(data, bytes):
                try:
                    return data.decode("utf-8")
                except Exception:
                    return data.decode("latin-1", errors="ignore")
            return str(data)
        except Exception:
            return None

    def update_challenge_config(self, challenge, changed_field):
        """
        Update challenge configuration in GitHub repository
        Only updates the specific field that changed
        """
        try:
            # Get existing challenge config to preserve structure
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
            
            # File fields logic (update the referenced file content)
            if changed_field in {"evaluation_script"}:
                file_path = config_data.get(changed_field)
                if not file_path:
                    logger.warning(f"No path for '{changed_field}' in challenge_config.yaml; skipping file update")
                    return False
                current_text = self.get_data_from_path(file_path)
                new_text = self._read_text_from_file_field(getattr(challenge, changed_field, None))
                if new_text is None or new_text == current_text:
                    logger.info(f"No content change for file field '{changed_field}'")
                    return True
                return True if self.update_data_from_path(file_path, new_text, changed_field) else False
            
            # Non-file field: update YAML key with processed value
            if hasattr(challenge, changed_field):
                current_value = getattr(challenge, changed_field)
                processed_value = self._process_field_value(changed_field, current_value)
                if processed_value is None:
                    logger.warning(f"Could not process changed field: {changed_field}")
                    return False
                # Skip if value unchanged to avoid empty commit
                if config_data.get(changed_field) == processed_value:
                    logger.info(f"No change detected for '{changed_field}', skipping commit")
                    return True
                config_data[changed_field] = processed_value
            else:
                logger.error(f"Field {changed_field} not found on challenge model")
                return False
            
            # Convert back to YAML
            yaml_content = yaml.dump(config_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Add documentation header
            header_comment = "# If you are not sure what all these fields mean, please refer our documentation here:\n# https://evalai.readthedocs.io/en/latest/configuration.html\n"
            yaml_content = header_comment + yaml_content
            
            # Update the file in GitHub
            success = self.update_data_from_path("challenge_config.yaml", yaml_content, changed_field)
            return True if success else False
                
        except Exception as e:
            logger.error(f"Error updating challenge config: {str(e)}")
            return False

    def update_challenge_phase_config(self, challenge_phase, changed_field):
        """
        Update challenge phase configuration in GitHub repository
        Only updates the specific field that changed
        """
        try:
            # Get existing challenge config to preserve structure
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
            
            # Locate the target phase by codename
            target_index = None
            for i, phase in enumerate(config_data['challenge_phases']):
                if phase.get('codename') == getattr(challenge_phase, 'codename', None):
                    target_index = i
                    break
            if target_index is None:
                logger.error(f"Phase with codename {getattr(challenge_phase, 'codename', None)} not found")
                return False
            
            # File field mapping in YAML
            yaml_key_map = {"test_annotation": "test_annotation_file"}
            yaml_key = yaml_key_map.get(changed_field, changed_field)
            
            # File field for phase: update referenced file content
            if changed_field in {"test_annotation"}:
                file_path = config_data['challenge_phases'][target_index].get(yaml_key)
                if not file_path:
                    logger.warning(f"No path for '{yaml_key}' in challenge_config.yaml; skipping file update")
                    return False
                current_text = self.get_data_from_path(file_path)
                new_text = self._read_text_from_file_field(getattr(challenge_phase, changed_field, None))
                if new_text is None or new_text == current_text:
                    logger.info(f"No content change for file field '{changed_field}' in phase")
                    return True
                return True if self.update_data_from_path(file_path, new_text, changed_field) else False
            
            # Non-file field: update YAML entry for that phase
            if hasattr(challenge_phase, changed_field):
                value = getattr(challenge_phase, changed_field)
                processed_value = self._process_field_value(changed_field, value)
                if processed_value is None:
                    logger.warning(f"Could not process changed phase field: {changed_field}")
                    return False
                # Skip if unchanged
                if config_data['challenge_phases'][target_index].get(yaml_key) == processed_value:
                    logger.info(f"No change detected for phase '{yaml_key}', skipping commit")
                    return True
                config_data['challenge_phases'][target_index][yaml_key] = processed_value
            else:
                logger.error(f"Field {changed_field} not found on challenge_phase model")
                return False
            
            # Convert back to YAML
            yaml_content = yaml.dump(config_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Update the file in GitHub
            success = self.update_data_from_path("challenge_config.yaml", yaml_content, changed_field)
            return True if success else False
                
        except Exception as e:
            logger.error(f"Error updating challenge phase config: {str(e)}")
            return False

    def _process_field_value(self, field, value):
        """
        Process a field value for GitHub sync
        Returns the processed value or None if processing failed
        """
        if value is None:
            return None
        
        try:
            if field in ['start_date', 'end_date'] and hasattr(value, 'strftime'):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            elif field in ['description', 'evaluation_details', 'terms_and_conditions', 'submission_guidelines'] and value:
                # Extract the actual content from HTML fields
                if hasattr(value, 'read'):
                    try:
                        value.seek(0)
                        content = value.read().decode('utf-8')
                        return content
                    except Exception:
                        return str(value)
                else:
                    return str(value)
            elif field in ['image', 'evaluation_script'] and value:
                # For YAML, store filename/path if available
                if hasattr(value, 'name'):
                    return value.name
                else:
                    return str(value)
            elif isinstance(value, (list, tuple)):
                clean_list = []
                for item in value:
                    if hasattr(item, 'pk'):
                        clean_list.append(item.pk)
                    elif hasattr(item, 'id'):
                        clean_list.append(item.id)
                    else:
                        clean_list.append(item)
                return clean_list
            else:
                if hasattr(value, 'pk'):
                    return value.pk
                elif hasattr(value, 'id'):
                    return value.id
                else:
                    return value
        except Exception as e:
            logger.error(f"Error processing field {field}: {str(e)}")
            return None