"""
This modules is to handle memsource using API
"""
import urllib.request
import json
import os
import ssl
from retry import retry

ssl._create_default_https_context = ssl._create_unverified_context

class APIException(Exception):
    """API Exception"""
    def __init__(self, message):
        self.message = message
class ProjectIDException(Exception):
    """Project ID Execption"""
    def __init__(self, message):
        self.message = message
class PreTranslateException(Exception):
    """Pretranslate Exception"""
    def __init__(self, message):
        self.message = message

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
        self.api_calls = 0
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

    def __call_rest(self, url, method, body=None, params=None, headers=None):
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

        # countup api calls
        self.api_calls = self.api_calls + 1

        # Prepare http request then POST
        req_url = '{0}?{1}'.format(url, urllib.parse.urlencode(params))
        request = urllib.request.Request(req_url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                content_type = ""
                response_header = response.getheaders()
                for head in response_header:
                    if head[0] == "Content-Type":
                        content_type = head[1]
                        break
                response_body = response.read().decode("utf-8")
                if response_body == "":
                    result = None
                elif content_type == "application/json":
                    result = json.loads(response_body.split('\n')[0])
                elif content_type == "application/octet-stream":
                    result = response_body
                elif content_type == "application/tmx":
                    result = response_body
                elif content_type == "":
                    result = str(response.getcode())
        except urllib.error.HTTPError as err:#If HTTP status code is 4xx or 5xx
            raise APIException(json.loads(err.read().decode('utf-8')))
        except urllib.error.URLError as err:#If HTTP connection is fails
            print(err)
            raise APIException(err)
        return result

    def get_job(self, project_uid, job_uid):
        """
        Get job datails
        Args:
            project_uid (str): project uid
            job_uid (str): job uid

        Returns:
            json: job datails
        """
        url = "https://cloud.memsource.com/web/api2/v1/projects/{}/jobs/{}".format(project_uid, job_uid)
        params = {'token': self.token}
        print('Getting "{}:{}" jobs datals...'.format(project_uid, job_uid))
        result = self.__call_rest(url, "GET", params=params)
        return result

    def get_workflow_steps(self, project_uid):
        """
        Get workflow level

        Returns:
            json: workflow level
        """

        url = "https://cloud.memsource.com/web/api2/v1/projects/{}/workflowSteps".format(project_uid)
        params = {'token': self.token}

        result = self.__call_rest(url, "GET", params=params)
        return result

    def list_projects(self):
        """
        Get All Project in Memsource

        Returns:
            json: project json
        """

        url = "https://cloud.memsource.com/web/api2/v1/projects/"
        params = {'token': self.token}

        result = self.__call_rest(url, "GET", params=params)
        return result

    def get_project(self, project_uid):
        """
        Get Project datails

        Args:
            project_uid (str): project UID
        """
        url = "https://cloud.memsource.com/web/api2/v1/projects/{}".format(project_uid)
        params = {'token': self.token}

        print('Getting "{}" project...'.format(project_uid))
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

    def get_segments(self, project_uid, job_uid, begin_index, end_index):
        """
        Get Segment data

        Args:
            project_uid (str): To get project UID
            job_uid (str): To get Job UID
            begin_index (int): Begin segment index
            end_index (int): End segment index

        Returns:
            json: segment data
        """

        url = "https://cloud.memsource.com/web/api2/v1/projects/{}/jobs/{}/segments".format(project_uid, job_uid)
        params = {'token': self.token, 'beginIndex': begin_index, 'endIndex': end_index}

        print('Getting "{}:{}:{}:{}" segment data...'.format(project_uid, job_uid, begin_index, end_index))
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

    def list_all_conversations(self, job_uid):
        """
        List all conversations in job

        Args:
            job_uid (str): Job id
        """
        url = "https://cloud.memsource.com/web/api2/v1/jobs/{}/conversations".format(job_uid)
        params = {'token': self.token}
        print('Getting concersations (job_uid: "{}")...'.format(job_uid))
        result = self.__call_rest(url, "GET", params=params)
        return result

    def download_tmx_file(self, tm_id):
        """
        Download tmx file with tm_id

        Args:
            tm_id (str): TM id
        """
        url = "https://cloud.memsource.com/web/api2/v1/transMemories/{}/export".format(tm_id)
        params = {'token': self.token}
        # headers = {"Content-Type" : "application/json"}
        print('Downloading TMX (tm_id: "{}")...'.format(tm_id))
        result = self.__call_rest(url, "GET", params=params)
        return result

    def create_tb(self, name, langs, client_id=None):
        """
        Get term bases

        Args:
            name ([str]): TM name
            langs ([list]): Languages
            client_id ([str], optional): client_id. Defaults to None.
        """
        url = "https://cloud.memsource.com/web/api2/v1/termBases"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "name": name,
            "langs": langs,
            }
        if client_id is not None:
            obj["client"] = {"id": client_id}
        result = self.__call_rest(url, "POST", body=obj, params=params, headers=headers)
        print("Creating TB {} ...".format(name))
        return result

    def upload_tb(self, tb_file_path, tb_id, charset="UTF-8", strictLangMatching="false", updateTerms="true"):
        """
        Upload tb file

        Args:
            tb_file_path (str): TB file path
        """

        url = "https://cloud.memsource.com/web/api2/v1/termBases/{}/upload".format(tb_id)
        params = {
            'token': self.token,
            'charset': charset,
            'strictLangMatching': strictLangMatching,
            'updateTerms': updateTerms
            }
        headers = {"Content-Type" : "application/octet-stream", "Content-Disposition" : "filename*=UTF-8''{}".format(os.path.basename(tb_file_path))}
        tb_file = open(tb_file_path, 'rb').read()
        result = self.__call_rest(url, "POST", body=tb_file, params=params, headers=headers)
        print("Uploading TB file {}...".format(tb_file))
        return result

    def create_tm(self, name, source_lang, target_lang, client_id=None):
        """
        Create TM

        Args:
            name ([str]): TM name
            source_lang ([str]): Source lang
            target_lang ([list]): Target Lang
            client_id ([str], optional): client_id. Defaults to None.
        """
        url = "https://cloud.memsource.com/web/api2/v1/transMemories"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "name": name,
            "sourceLang": source_lang,
            "targetLangs": target_lang,
            }
        if client_id is not None:
            obj["client"] = {"id": client_id}
        result = self.__call_rest(url, "POST", body=obj, params=params, headers=headers)
        print("Creating TM {} ...".format(name))
        return result

    def upload_tmx(self, tmx_file_path, tm_id):
        """
        Upload tmx file

        Args:
            tmx_file_path (str): tmx file path
        """

        url = "https://cloud.memsource.com/web/api2/v1/transMemories/{}/import".format(tm_id)
        params = {'token': self.token}
        headers = {"Content-Type" : "application/octet-stream", "Content-Disposition" : "filename*=UTF-8''{}".format(os.path.basename(tmx_file_path))}
        tmx_file = open(tmx_file_path, 'rb').read()
        result = self.__call_rest(url, "POST", body=tmx_file, params=params, headers=headers)
        print("Uploading TMX {}...".format(tmx_file_path))
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

    def search_tm(self, tm_id, query, source_lang, target_langs):
        """
        Search TM

        Args:
            tm_id (str): TM id
            query (str): Source string
            source_lang (str): Source language code
            target_langs ([list]): Target language codes

        Returns:
            json: result json
        """
        url = "https://cloud.memsource.com/web/api2/v1/transMemories/{}/search".format(tm_id)
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "query": query,
            "sourceLang": source_lang,
            "targetLangs": target_langs
        }
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def delete_tm(self, tm_id):
        """
        Delete TM

        Args:
            tm_id (str): TM id

        Returns:
            json: result json
        """
        url = "https://cloud.memsource.com/web/api2/v1/transMemories/{}".format(tm_id)
        params = {'token': self.token}
        result = self.__call_rest(url, "DELETE", params=params)
        return result

    def run_qa_batch(self, project_uid, job_uids):
        """
        Run batch QA

        Args:
            project_uid (str): Project uid
            job_uids (list): Job uids

        Returns:
            json: qa result
        """
        url = "https://cloud.memsource.com/web/api2/v3/projects/{}/jobs/qualityAssurances/run/".format(project_uid)
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "jobs": list(map(change_uid_to_dict, job_uids)),
            }
        result = self.__call_rest(url, "POST", body=obj, params=params, headers=headers)
        print("Unning QA (batch) {} ...".format(project_uid))
        return result

    @staticmethod
    def extract_segment_by_workflow_level(segment_dict, workflow_level):
        segment_list = []
        for segment in segment_dict["segments"]:
            if segment["workflowLevel"] == workflow_level:
                segment_list.append(segment)
        return segment_list

def change_uid_to_dict(uid):
    """
    Chnage UID to dict
    Args:
        uid (str): uid

    Returns:
        dict: uid with uid key dict
    """
    return {'uid': uid}

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
        raise ProjectIDException('Project id "{}" is not found in Memsource ...'.format(internal_id))
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
