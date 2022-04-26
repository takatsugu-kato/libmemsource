"""
This modules is to handle memsource using API
"""
import urllib.request
import json
import os
import ssl
import copy
from datetime import date
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
class AsyncRequestException(Exception):
    """AsyncRequestException Exception"""
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
        encoded_param = urllib.parse.urlencode(params)
        req_url = f'{url}?{encoded_param}'
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
                elif content_type == "application/tbx":
                    result = response_body
                elif content_type == "":
                    result = str(response.getcode())
        except urllib.error.HTTPError as err:#If HTTP status code is 4xx or 5xx
            raise APIException(json.loads(err.read().decode('utf-8')))
        except urllib.error.URLError as err:#If HTTP connection is fails
            print(err)
            raise APIException(err)
        return result

    def get_termbase(self, termbase_uid):
        """Get termbase

        Args:
            termbase_uid (int): tertmbase uid
        """
        url = f"https://cloud.memsource.com/web/api2/v1/termBases/{termbase_uid}"
        params = {'token': self.token}
        print(f'Getting tb "{termbase_uid}"...')
        result = self.__call_rest(url, "GET", params=params)
        return result

    def export_termbase(self, termbase_uid, export_format="Tbx"):
        """
        Export termbase

        Args:
            termbase_uid (int): termbase uid
            format (str, optional): Tbx, Xlsx. Defaults to "Tbx".
        """
        url = f"https://cloud.memsource.com/web/api2/v1/termBases/{termbase_uid}/export"
        params = {'token': self.token, 'format': export_format}
        print(f'Download tb "{termbase_uid}"...')
        result = self.__call_rest(url, "GET", params=params)
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
        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/jobs/{job_uid}"
        params = {'token': self.token}
        print(f'Getting "{project_uid}:{job_uid}" jobs datals...')
        result = self.__call_rest(url, "GET", params=params)
        return result

    def get_workflow_steps(self, project_uid):
        """
        Get workflow level

        Returns:
            json: workflow level
        """

        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/workflowSteps"
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

    def create_project_from_template(self, template_uid:str, name:str, source_lang:str=None, target_langs:list=None, workflow_steps:list=None, date_due:date=None, note:str=None, client_id:str=None):
        """Create Project from Template

        Args:
            template_uid (str): template uid
            name (str): project name
            source_lang (str, optional): Source language code. Defaults to None.
            target_langs (list, optional): Target language code. Defaults to None.
            workflow_steps (list, optional): Workflow steps uids. Defaults to None.
            date_due (date, optional): Due date. Defaults to None.
            note (str, optional): Project note. Defaults to None.
            client_id (str, optional): Client UID. Defaults to None.

        Returns:
            dict: Admin Project Manager V2
        """
        url = f"https://cloud.memsource.com/web/api2/v2/projects/applyTemplate/{template_uid}"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}

        if workflow_steps is None:
            workflow_steps = []
        obj =  {
                "name": name,
                "sourceLang": source_lang,
                "targetLangs": target_langs,
                "workflowSteps": list(map(change_id_to_dict, workflow_steps)),
                "dateDue": date_due,
                "note": note,
            }
        if client_id:
            obj["client"] = {"id": client_id}

        print(f'Creating project using {template_uid}...')
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def get_project(self, project_uid):
        """
        Get Project datails

        Args:
            project_uid (str): project UID
        """
        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}"
        params = {'token': self.token}

        print(f'Getting "{project_uid}" project...')
        result = self.__call_rest(url, "GET", params=params)
        return result

    def create_job(self, source_file_path:str, project_uid:str, target_langs:list, due:date=None, workflow_settings:list=None, assignments:list=None, import_settings:dict=None, use_project_file_import_settings:bool=None, callback_url:str=None, path:str=None, pre_translate:bool=None):
        """Create Job

        Args:
            source_file_path (str): Source file path
            project_uid (str): Project UID
            target_langs (list): List of target locale code
            due (date, optional): Due date. Defaults to None.
            workflow_settings (list, optional): Workflow settings. Defaults to None.
                                                "workflowSettings": [
                                                    {
                                                        "id": "64",
                                                        "due": "2007-12-03T10:15:30.00Z",
                                                        "assignments": [
                                                            {
                                                            "targetLang": "de",
                                                            "providers": [
                                                                {
                                                                "id": "3",
                                                                "type": "VENDOR"
                                                                }
                                                            ]
                                                            }
                                                        ],
                                                        "notifyProvider": {
                                                            "organizationEmailTemplate": {
                                                            "id": "39"
                                                            },
                                                            "notificationIntervalInMinutes": "10"
                                                        }
                                                    }
                                                ]
            assignments (list, optional): Assignments. Defaults to None.
                                            "assignments": [
                                                    {
                                                    "targetLang": "cs_cz",
                                                    "providers": [
                                                        {
                                                        "id": "4321",
                                                        "type": "USER"
                                                        }
                                                    ]
                                                }
                                            ],
            import_settings (dict, optional): Import Settings. Defaults to None. see Create import settings (https://cloud.memsource.com/web/docs/api#operation/createImportSettings)
            use_project_file_import_settings (bool, optional): Use project file import settings. Defaults to None.
            callback_url (str, optional): Callback URL. Defaults to None.
            path (str, optional): original destination directory. Defaults to None.
            pre_translate (bool, optional): set pre translate job after import. Defaults to None.

        Returns:
            _type_: _description_
        """
        params = {'token': self.token}
        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/jobs"

        if workflow_settings is None:
            workflow_settings = []
        if assignments is None:
            assignments = []

        memsource =  {
                "targetLangs" : target_langs,
                "due" : due,
                "workflowSettings" : workflow_settings,
                "assignments" : assignments,
                "importSettings" : import_settings,
                "useProjectFileImportSettings" : use_project_file_import_settings,
                "callbackUrl" : callback_url,
                "path" : path,
                "preTranslate" : pre_translate,
            }
        filename = os.path.basename(source_file_path)
        headers = {
            "Content-Type" : "application/octet-stream",
            "Content-Disposition" : f"filename*=UTF-8''{filename}",
            "Memsource" : json.dumps(memsource),
            }

        source_file = open(source_file_path, 'rb').read()
        print('Creating job ...')
        result = self.__call_rest(url, "POST", body=source_file, params=params, headers=headers)
        return result


    def list_jobs(self, project_uid, workflow_level=1, page_number=0, prev_result=None):
        """
        Get jobs list in project

        Args:
            project_uid (str): To get project UID
            workflow_level (int): To get workflow level

        Returns:
            json: jobs list in project
        """
        url = f"https://cloud.memsource.com/web/api2/v2/projects/{project_uid}/jobs"
        params = {'token': self.token, 'workflowLevel': workflow_level, 'pageNumber': page_number}

        print(f'Getting "{project_uid}:{workflow_level}:{page_number}" jobs list...')
        result = self.__call_rest(url, "GET", params=params)

        if not prev_result is None:
            prev_result['content'].extend(result['content'])
            result['content'] = prev_result['content']

        # 全ファイルを再帰処理する
        if result['totalPages'] - 1 > result['pageNumber']:
            self.list_jobs(project_uid, workflow_level, page_number + 1, result)

        return result

    def create_analysis(self, job_uids:list, analysis_type="PreAnalyse", include_fuzzy_repetitions=True, include_confirmed_segments=True, include_numbers=True, include_locked_segments=True, count_source_units=True, include_trans_memory=True, include_non_translatables=True, include_machine_translation_matches=True, trans_memory_post_editing=True, non_translatable_post_editing=True, machine_translate_post_editing=True, name="Analysis #{innerId}"):
        """Create Analysis

        Args:
            job_uids (list): job uid list
            analysis_type (str, optional): [description]. Defaults to "PreAnalyse". Enum: "PreAnalyse" "PostAnalyse" "Compare".
            include_fuzzy_repetitions (bool, optional): [description]. Defaults to True.
            include_confirmed_segments (bool, optional): [description]. Defaults to True.
            include_numbers (bool, optional): [description]. Defaults to True.
            include_locked_segments (bool, optional): [description]. Defaults to True.
            count_source_units (bool, optional): [description]. Defaults to True.
            include_trans_memory (bool, optional): [description]. Defaults to True.
            include_non_translatables (bool, optional): [description]. Defaults to True.
            include_machine_translation_matches (bool, optional): [description]. Defaults to True.
            trans_memory_post_editing (bool, optional): [description]. Defaults to True.
            non_translatable_post_editing (bool, optional): [description]. Defaults to True.
            machine_translate_post_editing (bool, optional): [description]. Defaults to True.
            name (str, optional): [description]. Defaults to "Analysis #{innerId}".

        Returns:
            json: asyncRequests
        """
        url = "https://cloud.memsource.com/web/api2/v2/analyses"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}

        obj = {
            "jobs": [{"uid": job_uid} for job_uid in job_uids],
            "includeFuzzyRepetitions": include_fuzzy_repetitions,
            "includeConfirmedSegments": include_confirmed_segments,
            "includeNumbers": include_numbers,
            "includeLockedSegments": include_locked_segments,
            "countSourceUnits": count_source_units,
            "includeTransMemory": include_trans_memory,
            "includeNonTranslatables": include_non_translatables,
            "includeMachineTranslationMatches": include_machine_translation_matches,
            "transMemoryPostEditing": trans_memory_post_editing,
            "nonTranslatablePostEditing": non_translatable_post_editing,
            "machineTranslatePostEditing": machine_translate_post_editing,
            "name": name,
            }

        print('Creating analysis ...')
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def assigns_providers_from_template(self, project_uid, template_uid):
        """Assigns providers from template

        Args:
            project_uid (str): Project UID
            template_uid (str): Template UID

        Returns:
            json: jobs data
        """
        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/applyTemplate/{template_uid}/assignProviders"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}

        print('Assigning providers from template ...')
        result = self.__call_rest(url, "POST", params=params, body=None, headers=headers)
        return result

    def assigns_providers_from_template_specific_jobs(self, project_uid, template_uid, job_uids):
        """Assigns providers from template

        Args:
            project_uid (str): Project UID
            template_uid (str): Template UID
            job_uids (list): Job UIDs

        Returns:
            json: jobs data
        """
        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/applyTemplate/{template_uid}/assignProviders/forJobParts"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "jobs": list(map(change_uid_to_dict, job_uids)),
            }
        print('Assigning providers from template ...')
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def get_analysis(self, analysis_id):
        """Get analysis

        Args:
            analysis_id (int): analysis ID

        Returns:
            json: analysis result
        """
        url = f"https://cloud.memsource.com/web/api2/v3/analyses/{analysis_id}"
        params = {'token': self.token, 'format': format}

        print(f'Getting "{analysis_id}" analysis...')
        result = self.__call_rest(url, "GET", params=params)
        return result

    def download_analysis(self, analysis_id, log_format="CSV_EXTENDED"):
        """Download analysis

        Args:
            analysis_id (int): analysis ID
            log_format (str, optional): analysis format. Defaults to "CSV_EXTENDED". Enum: "CSV" "CSV_EXTENDED" "LOG" "JSON"

        Returns:
            [type]: [description]
        """
        url = f"https://cloud.memsource.com/web/api2/v1/analyses/{analysis_id}/download"
        params = {'token': self.token, 'format': log_format}

        print(f'Downloading "{analysis_id}" analysis...')
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

        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/jobs/{job_uid}/segments"
        params = {'token': self.token, 'beginIndex': begin_index, 'endIndex': end_index}

        print(f'Getting "{project_uid}:{job_uid}:{begin_index}:{end_index}" segment data...')
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

        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/jobs/preTranslate"
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

        print(f'Pretranslating (jobids: "{job_uids}") in (projectid: "{project_uid}") ...')
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

        url = f"https://cloud.memsource.com/web/api2/v1/async/{async_request_id}"
        params = {'token': self.token}

        result = self.__call_rest(url, "GET", params=params)
        return result

    def list_all_conversations(self, job_uid):
        """
        List all conversations in job

        Args:
            job_uid (str): Job id
        """
        url = f"https://cloud.memsource.com/web/api2/v1/jobs/{job_uid}/conversations"
        params = {'token': self.token}
        print(f'Getting concersations (job_uid: "{job_uid}")...')
        result = self.__call_rest(url, "GET", params=params)
        return result

    def download_tmx_file(self, tm_id):
        """
        Download tmx file with tm_id

        Args:
            tm_id (str): TM id
        """
        url = f"https://cloud.memsource.com/web/api2/v1/transMemories/{tm_id}/export"
        params = {'token': self.token}
        # headers = {"Content-Type" : "application/json"}
        print(f'Downloading TMX (tm_id: "{tm_id}")...')
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
        print(f"Creating TB {name} ...")
        return result

    def upload_tb(self, tb_file_path, tb_id, charset="UTF-8", strict_lang_matching="false", update_terms="true"):
        """
        Upload tb file

        Args:
            tb_file_path (str): TB file path
        """

        url = f"https://cloud.memsource.com/web/api2/v1/termBases/{tb_id}/upload"
        params = {
            'token': self.token,
            'charset': charset,
            'strictLangMatching': strict_lang_matching,
            'updateTerms': update_terms
            }
        filename = os.path.basename(tb_file_path)
        headers = {"Content-Type" : "application/octet-stream", "Content-Disposition" : f"filename*=UTF-8''{filename}"}
        tb_file = open(tb_file_path, 'rb').read()
        result = self.__call_rest(url, "POST", body=tb_file, params=params, headers=headers)
        print(f"Uploading TB file {tb_file_path}...")
        return result

    def edit_tb(self, tb_id, name, langs):
        """Edit TB

        Args:
            tb_id (str): TB id
            name (str): TB name
            langs (list): languages

        Returns:
            obj: result obj
        """
        url = f"https://cloud.memsource.com/web/api2/v1/termBases/{tb_id}"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "name": name,
            "langs": langs,
        }
        result = self.__call_rest(url, "PUT", body=obj, params=params, headers=headers)
        print(f"Editing TB {name}...")
        return result

    def clear_tb(self, tb_id):
        """
        Delete TM

        Args:
            tb_id (str): TB id

        Returns:
            json: result json
        """
        url = f"https://cloud.memsource.com/web/api2/v1/termBases/{tb_id}/terms"
        params = {'token': self.token}
        result = self.__call_rest(url, "DELETE", params=params)
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
        print(f"Creating TM {name} ...")
        return result

    def upload_tmx(self, tmx_file_path, tm_id):
        """
        Upload tmx file

        Args:
            tmx_file_path (str): tmx file path
        """

        url = f"https://cloud.memsource.com/web/api2/v1/transMemories/{tm_id}/import"
        params = {'token': self.token}
        filename = os.path.basename(tmx_file_path)
        headers = {"Content-Type" : "application/octet-stream", "Content-Disposition" : f"filename*=UTF-8''{filename}"}
        tmx_file = open(tmx_file_path, 'rb').read()
        result = self.__call_rest(url, "POST", body=tmx_file, params=params, headers=headers)
        print(f"Uploading TMX {tmx_file_path}...")
        return result

    def download_mxlf_file(self, project_uid, job_uid):
        """
        Download mxlf file with jobs_uid filename

        Args:
            project_uid (str): Project UID
            job_uid (str): Job UID
        """

        url = f"https://cloud.memsource.com/web/api2/v1/projects/{project_uid}/jobs/bilingualFile"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {"jobs": [{"uid": job_uid}]}

        print(f'Downloading mxlf file (jobid: "{job_uid}") in (projectid: "{project_uid}")...')
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
        print(f'Uploading "{mxlf_file_path}" ...')
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
        url = f"https://cloud.memsource.com/web/api2/v1/transMemories/{tm_id}/search"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "query": query,
            "sourceLang": source_lang,
            "targetLangs": target_langs
        }
        result = self.__call_rest(url, "POST", params=params, body=obj, headers=headers)
        return result

    def add_target_language_to_tm(self, tm_id, target_lang):
        """Add target language to TM

        Args:
            tm_id (str): TM uid
            target_lang (str): target language

        Returns:
            json: result json
        """
        url = f"https://cloud.memsource.com/web/api2/v1/transMemories/{tm_id}/targetLanguages"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "language": target_lang
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
        url = f"https://cloud.memsource.com/web/api2/v1/transMemories/{tm_id}"
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
        url = f"https://cloud.memsource.com/web/api2/v3/projects/{project_uid}/jobs/qualityAssurances/run/"
        params = {'token': self.token}
        headers = {"Content-Type" : "application/json"}
        obj = {
            "jobs": list(map(change_uid_to_dict, job_uids)),
            }
        result = self.__call_rest(url, "POST", body=obj, params=params, headers=headers)
        print(f"Running QA (batch) {project_uid} ...")
        return result

    @staticmethod
    def extract_segment_by_workflow_level(segment_dict, workflow_level):
        """Extract segment by workflow level

        Args:
            segment_dict (dict): Segment dic
            workflow_level (int): Workflow level

        Returns:
            list: Segment list
        """
        segment_list = []
        for segment in segment_dict["segments"]:
            if segment["workflowLevel"] == workflow_level:
                segment_list.append(segment)
        return segment_list

def change_uid_to_dict(uid):
    """
    Change UID to dict
    Args:
        uid (str): uid

    Returns:
        dict: uid with uid key dict
    """
    return {'uid': uid}

def change_id_to_dict(v_id):
    """
    Change ID to dict
    Args:
        v_id (str): id

    Returns:
        dict: id with uid key dict
    """
    return {'id': v_id}

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
        print(f'Project id "{internal_id}" is not found in Memsource ...')
        raise ProjectIDException(f'Project id "{internal_id}" is not found in Memsource ...')
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
def check_async_is_complete(memsource_api, async_req_id):
    """
    Check async request is complete

    Args:
        memsource_api (obj): memsource_api object
        async_req_id (str): async request id

    Raises:
        AsyncRequestException: [description]
    """

    result = memsource_api.get_async_request(async_req_id)
    if result['asyncResponse']:
        print(f'Async request of "{async_req_id}" is completed.')
        return True
    else:
        raise AsyncRequestException(f'Async request of "{async_req_id}"  has not been completed yet')
