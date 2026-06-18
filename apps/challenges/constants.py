SUPPORTED_WORKER_PYTHON_VERSIONS = ("3.7", "3.8", "3.9")
DEFAULT_WORKER_PYTHON_VERSION = "3.9"

# Django settings module suffixes that differ from ECR repository env names.
SETTINGS_ENV_TO_ECR_ENV = {
    "prod": "production",
}


def get_ecr_env_name(settings_env, override=None):
    """
    Map a Django settings suffix (e.g. prod) to the ECR repo env (e.g. production).
    """
    if override:
        return override
    return SETTINGS_ENV_TO_ECR_ENV.get(settings_env, settings_env)
