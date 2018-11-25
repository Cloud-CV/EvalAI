import os
import tempfile
import urllib.request

from .models import Submission

from base.utils import get_model_object

get_submission_model = get_model_object(Submission)


def url_is_valid(url):
    """
    Checks that a given URL is reachable.
    :param url: A URL
    :return type: bool
    """
    request = urllib.request.Request(url)
    request.get_method = lambda: 'HEAD'
    try:
        urllib.request.urlopen(request)
        return True
    except urllib.request.HTTPError:
        return False


def get_file_from_url(url):
    BASE_TEMP_DIR = tempfile.mkdtemp()
    file_name  = url.split("/")[-1]
    file_path = os.path.join(BASE_TEMP_DIR, file_name)
    file_obj = {}
    filename, headers = urllib.request.urlretrieve(url, file_path)
    file_obj['name'] = filename
    file_obj['headers'] = headers
    file_obj['temp_dir_path'] = BASE_TEMP_DIR
    return file_obj
