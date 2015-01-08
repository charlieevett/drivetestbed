import base64
import uuid
from apiclient.errors import HttpError
from httplib2 import Response

__author__ = 'charlie'


class ServiceCall(object):

    def __init__(self, meth, **kwargs):
        self._callable = meth
        self._kwargs = kwargs

    def execute(self):
        return self._callable(**self._kwargs)


# From Stack Overflow: http://stackoverflow.com/questions/534839/how-to-create-a-guid-in-python
# get a UUID - URL safe, Base64
def get_a_uuid():
    r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    return r_uuid.replace('=', '')


class FilesService(object):

    def __init__(self, files=None):
        self._files = {}
        files = files or []
        for afile in files:
            if 'id' not in afile:
                afile['id'] = get_a_uuid()
            self._files[afile['id']] = afile

    def _list(self, **kwargs):
        response = {
            "kind": "drive#fileList",
            "etag": "\"ALmZNavQ1pakoTwofyfJ4wBG6iY/vyGp6PvFo4RvsFtPoIWeCReyIC8\"",
            "selfLink": "https://www.googleapis.com/drive/v2/files?q=trashed+%3D+false",
            "items": self._files.values()
        }
        return response

    def list(self, **kwargs):
        return ServiceCall(self._list, **kwargs)

    def _insert(self, body=None, **kwargs):
        # todo -- handle error for body
        response = {
            "kind": "drive#file",
            "title": body.get('title'),
            "description": body.get("description"),
            "mimeType": body.get("mimeType", "application/octet-stream")
        }
        response['id'] = get_a_uuid()
        self._files[response['id']] = response
        return response

    def insert(self, **kwargs):
        return ServiceCall(self._insert, **kwargs)

    def raise_404(self, fileId):
        resp = Response({"status": 404, "reason": "Not Found"})
        raise HttpError(resp,
                        '''
                        {
                         "error": {
                          "errors": [
                           {
                            "domain": "global",
                            "reason": "notFound",
                            "message": "File not found: %(fileId)s"
                           }
                          ],
                          "code": 404,
                          "message": "File not found: %(fileId)s"
                         }
                        }''' % {"fileId": fileId})

    def _get(self, fileId=None, **kwargs):
        file = self._files.get(fileId)
        if file:
            return file
        else:
            self.raise_404(fileId)

    def get(self, fileId=None, **kwargs):
        return ServiceCall(self._get, **kwargs)

    def _delete(self, fileId=None, **kwargs):
        if fileId not in self._files:
            self.raise_404(fileId)
        del self._files[fileId]
        return {}

    def delete(self, fileId=None, **kwargs):
        return ServiceCall(self._delete, fileId=fileId, **kwargs)

    def _copy(self, fileId=None, body=None, **kwargs):
        if fileId not in self._files:
            self.raise_404(fileId)
        file_copy = self._files[fileId].copy()
        if body:
            for key in body.keys():
                file_copy[key] = body[key]
        return self._insert(body=file_copy)

    def copy(self, fileId=None, **kwargs):
        return ServiceCall(self._copy, fileId=fileId, **kwargs)


class ServiceDirectory(object):

    def __init__(self, files=None):
        self._files = FilesService(files=files)

    def files(self):
        return self._files


class ServiceStub(object):

    # TODO -- add something to create a fixture service with pre-set files, etc.

    @classmethod
    def get_service(cls, files=None):
        '''
        This creates a new empty service every time
        :return:
        '''
        return ServiceDirectory(files=files)
