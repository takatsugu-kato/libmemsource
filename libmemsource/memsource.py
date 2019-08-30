"""
This modules is to handle memsource using API
"""
import urllib.request
import json
import ssl
from retry import retry

ssl._create_default_https_context = ssl._create_unverified_context

class APIException(Exception):
    """API Exception"""
class ProjectIDException(Exception):
    """Project ID Execption"""
class PreTranslateException(Exception):
    """Pretranslate Exception"""

class MemsourceAPI:
    """
    Object handling Memsource API

    Args:
        username (str): Memsoruce username
        password (str): Memsoruce password
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = ""
        result = self.__get_token()
        self.token = result['token']

    def __get_token(self):
        """
        Get memsource token

        Returns:
            str: Memsource token
        """

        url = "https://cloud.memsource.com/web/api2/v1/auth/login"
        headers = {"Content-Type" : "application/json"}
        obj = {"userName" : self.username, "password" : self.password}

        print('Loging to Memsource...')
        result = self.__call_rest(url, "POST", body=obj, headers=headers)
        return result

    @staticmethod
    def __call_rest(url, method, body=None, params=None, headers=None):
        """
        Call REST using urllib.request

        Args:
            url (str): url
            method (str): POST or GET
            body (dict or something, optional): Defaults to None. request body
            params (dict, optional): Defaults to None. query paramaeters
            headers (dict, optional): Defaults to None. request headers

        Returns:
            json or str: If response content type is json, return json. else if octet-stream return response body as str.
        """
        if params is None:
            params = {}
        if headers is None:
            headers = {}

        if isinstance(body, dict):# Convert Python object to JSON
            data = json.dumps(body).encode("utf-8")
        elif body is None:
            data = None
        else:
            data = body

        # Prepare http request then POST
        req_url = '{0}?{1}'.format(url, urllib.parse.urlencode(params))
        request = urllib.request.Request(req_url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                response_header = response.getheaders()
                for head in response_header:
                    if head[0] == "Content-Type":
                        content_type = head[1]
                        break
                response_body = response.read().decode("utf-8")
                if content_type == "application/json":
                    result = json.loads(response_body.split('\n')[0])
                elif content_type == "application/octet-stream":
                    result = response_body
        except urllib.error.HTTPError as err:#If HTTP status code is 4xx or 5xx
            print(err)
            raise APIException(err)
        except urllib.error.URLError as err:#If HTTP connection is fails
            print(err)
            raise APIException(err)
        return result

    def get_project(self):
        """
        Get All Project in Memsource

        Returns:
            json: project json
        """

        url = "https://cloud.memsource.com/web/api2/v1/projects/"
        params = {'token': self.token}

        result = self.__call_rest(url, "GET", params=params)
        return result

    def list_jobs(self, project_uid, workflow_level=1):
        """
        Get jobs list in project

        Args:
            project_uid (str): To get project UID
            workflow_level (int): To get workflow level

        Returns:
            json: jobs list in project
        """

        url = "https://cloud.memsource.com/web/api2/v2/projects/{}/jobs".format(project_uid)
        params = {'token': self.token, 'workflowLevel': workflow_level}

        print('Getting "{}" jobs list...'.format(project_uid))
        result = self.__call_rest(url, "GET", params=params)
        return result

    def pretranslate_using_tm(self, project_uid, job_uids):
        """
        Pretranslate jobs using tm

        Args:
            project_uid (str): To get project UID

        Returns:
            json: jobs list in project
        """

        url = "https://cloud.memsource.com/web/api2/v1/projects/{}/jobs/preTranslate".format(project_uid)
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "jobs": job_uids,
            "useTranslationMemory": "true",
            "useMachineTranslation": "false",
            "translationMemoryTreshold": 0.75,
            "preTranslateNonTranslatables": "true",
            "confirm100NonTranslatableMatches": "true",
            "segmentFilters": [
                "NOT_LOCKED"
            ]
            }

        print('Pretranslating (jobids: "{}") in (projectid: "{}") ...'.format(job_uids, project_uid))
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def get_async_request(self, async_request_id):
        """
        get async request

        Args:
            async_request_id (int): To get async request id

        Returns:
            json: async Response
        """

        url = "https://cloud.memsource.com/web/api2/v1/async/{}".format(async_request_id)
        params = {'token': self.token}

        result = self.__call_rest(url, "GET", params=params)
        return result

    def download_mxlf_file(self, project_uid, job_uid):
        """
        Download mxlf file with jobs_uid filename

        Args:
            project_uid (str): Project UID
            job_uid (str): Job UID
        """

        url = "https://cloud.memsource.com/web/api2/v1/projects/{}/jobs/bilingualFile".format(project_uid)
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {"jobs": [{"uid": job_uid}]}

        print('Downloading mxlf file (jobid: "{}") in (projectid: "{}")...'.format(job_uid, project_uid))
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def upload_mxlf_file(self, mxlf_file_path):
        """
        Upload mxlf file

        Args:
            mxlf_file_path (str): mxlf file path

        Returns:
            json: result json
        """

        url = "https://cloud.memsource.com/web/api2/v1/bilingualFiles"
        params = {'token': self.token, 'saveToTransMemory': "None"}
        headers = {"Content-Type" : "application/octet-stream"}
        mxlf_file_obj = open(mxlf_file_path, "rb")
        print('Uploading "{}" ...'.format(mxlf_file_path))
        result = self.__call_rest(url, "PUT", body=mxlf_file_obj, params=params, headers=headers)
        mxlf_file_obj.close()
        return result

def get_index_from_value_and_key(data, val, key, value_type):
    """
    Get index from value and key

    Args:
        data (list): list
        val (str): value
        key (str): key
        value_type (type): value type

    Returns:
        int or None: index number
    """

    index = None
    for i, project_dict in enumerate(data):
        if project_dict[key] == value_type(val):
            index = i
    if index is not None:
        return index
    return None

def get_project_content(project_list, internal_id, key):
    """
    Get project content by internal id

    Args:
        project_list (json): Project list json
        internal_id (str): internal id
        key (str): to get content json key

    Returns:
        str: Project uid
    """

    index = get_index_from_value_and_key(project_list['content'], internal_id, "internalId", type(0))
    if index is None:
        print('Project id "{}" is not found in Memsource ...'.format(internal_id))
        raise ProjectIDException()
    return project_list['content'][index][key]

def pretranslate_project(memsource_api, project_uid, jobs_list):
    """
    Pretranslate project

    Args:
        memsource_api (obj): memsource_api object
        project_uid (str): project uid
        jobs_list (list): jobs list

    Returns:
        str: asyncRequest id
    """

    job_ids = []
    for job in jobs_list['content']:
        job_ids.append({"uid": job['uid']})
    result = memsource_api.pretranslate_using_tm(project_uid, job_ids)
    return result['asyncRequest']['id']

@retry(tries=60, delay=10)
def check_async_pretranslate_is_complete(memsource_api, async_req_id, project_uid):
    """
    Check async pretransalte is complete

    Args:
        memsource_api (obj): memsource_api object
        async_req_id (str): async request id
        project_uid (str): project uid for only using logging

    Raises:
        PreTranslateException: [description]
    """

    result = memsource_api.get_async_request(async_req_id)
    if result['asyncResponse']:
        print('Pretranslate of "{}" is completed.'.format(project_uid))
    else:
        raise PreTranslateException('Pretranslate of "{}" has not been completed yet'.format(project_uid))
