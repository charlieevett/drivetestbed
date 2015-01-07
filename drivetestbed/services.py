import base64
import uuid
from apiclient.errors import HttpError
from httplib2 import Response

__author__ = 'charlie'


class ServiceCall(object):

    def __init__(self, response):
        self._response = response

    def execute(self):
        return self._response


# From Stack Overflow: http://stackoverflow.com/questions/534839/how-to-create-a-guid-in-python
# get a UUID - URL safe, Base64
def get_a_uuid():
    r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    return r_uuid.replace('=', '')


class FilesService(object):

    def __init__(self):
        self._files = {}

    def list(self, **kwargs):
        empty_response = {
             "kind": "drive#fileList",
             "etag": "\"ALmZNavQ1pakoTwofyfJ4wBG6iY/vyGp6PvFo4RvsFtPoIWeCReyIC8\"",
             "selfLink": "https://www.googleapis.com/drive/v2/files?q=trashed+%3D+false",
             "items": [
             ]
        }
        return ServiceCall(empty_response)

    def insert(self, body=None, **kwargs):
        # todo -- handle error for body
        response = {
            "kind": "drive#file",
            "title": body.get('title'),
            "description": body.get("description"),
            "mimeType": body.get("mimeType", "application/octet-stream")
        }
        response['id'] = get_a_uuid()
        self._files[response['id']] = response
        return ServiceCall(response)

    def get(self, fileId=None, **kwargs):
        file = self._files.get(fileId)
        if file:
            return ServiceCall(file)
        else:
            resp = Response({"status": 401, "reason": "File not found"})
            raise HttpError(resp, "File not found")


class ServiceDirectory(object):

    def __init__(self):
        self._files = FilesService()

    def files(self):
        return self._files


THE_SERVICE = ServiceDirectory()


class ServiceStub(object):

    @classmethod
    def get_service(cls):
        return THE_SERVICE
