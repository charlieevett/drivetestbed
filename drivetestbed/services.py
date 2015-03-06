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


def raise_404(fileId, msg=None):
    if not msg:
        msg = "File not found: %s" % fileId
    resp = Response({"status": 404, "reason": "Not Found"})
    raise HttpError(resp,
                    '''
                    {
                     "error": {
                      "errors": [
                       {
                        "domain": "global",
                        "reason": "notFound",
                        "message": "%(msg)s"
                       }
                      ],
                      "code": 404,
                      "message": "%(msg)s"
                     }
                    }''' % {"msg": msg})


class FilesService(object):

    def __init__(self, files=None, directory=None, user_email="test@gmail.com"):
        self._files = {}
        self.path = "files"
        files = files or []
        for afile in files:
            if 'id' not in afile:
                afile['id'] = get_a_uuid()
            self._files[afile['id']] = afile
        self._directory = directory

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
        self._directory.permissions()._set_default_permissions(response)
        self._directory.parents()._set_default_parent(response)
        return response

    def insert(self, **kwargs):
        return ServiceCall(self._insert, **kwargs)

    def _get(self, fileId=None, **kwargs):
        file = self._files.get(fileId)
        if file:
            return file
        else:
            raise_404(fileId)

    def get(self, fileId=None, **kwargs):
        return ServiceCall(self._get, **kwargs)

    def _delete(self, fileId=None, **kwargs):
        if fileId not in self._files:
            raise_404(fileId)
        del self._files[fileId]
        return {}

    def delete(self, fileId=None, **kwargs):
        return ServiceCall(self._delete, fileId=fileId, **kwargs)

    def _copy(self, fileId=None, body=None, **kwargs):
        if fileId not in self._files:
            raise_404(fileId)
        file_copy = self._files[fileId].copy()
        if body:
            for key in body.keys():
                file_copy[key] = body[key]
        return self._insert(body=file_copy)

    def copy(self, fileId=None, **kwargs):
        return ServiceCall(self._copy, fileId=fileId, **kwargs)

    def request(self, path, method='GET', **kwargs):
        """
        :param uri: The parsed URI of the request
        :param method:
        :return:
        """
        if path.endswith("files"):
            return self._list()




class PermissionsService(object):

    def __init__(self, files=None, directory=None):
        self._directory = directory
        self._permissions = {}
        files = files or []
        for afile in files:
            self._set_default_permissions(afile)

    def _set_default_permissions(self, afile):
        # TODO -- create scheme to set up current user
        default_perms = [
            {
               "kind": "drive#permission",
               "etag": "Lie3Y624-6bAlCGsnUSYyb6P-dU/k6w2imYTYLSrsTHqeiu6HpWiCVQ",
               "id": "11519106257625907838",
               "name": "Test User",
               "emailAddress": self._directory._user_email,
               "domain": "testers.com",
               "role": "owner",
               "type": "user",
            }
        ]
        self._permissions[afile['id']] = default_perms

    def _get(self, fileId=None, permissionId=None, **kwargs):
        if fileId not in self._permissions:
            raise_404(fileId)
        perms = self._permissions[fileId]
        for permission in perms:
            if permission['id'] == permissionId:
                return permission
        raise_404(fileId, msg="Permission not found: %s" % permissionId)

    def get(self, fileId=None, **kwargs):
        return ServiceCall(self._get, fileId=fileId, **kwargs)

    def _list(self, fileId=None, **kwargs):
        if fileId not in self._permissions:
            raise_404(fileId)
        response = {
            "kind": "drive#permissionList",
            "etag": "AFakeETag",
            "items": self._permissions[fileId]
        }
        return response

    def list(self, fileId=None, **kwargs):
        return ServiceCall(self._list, fileId=fileId, **kwargs)

    def _getIdForEmail(self, email=None, **kwargs):
        response = {
            "kind": "drive#permissionId",
            "id": str(hash(email))
        }
        return response

    def getIdForEmail(self, email=None, **kwargs):
        return ServiceCall(self._getIdForEmail, email=email, **kwargs)

    def _insert(self, fileId=None, body=None, **kwargs):
        if fileId not in self._permissions:
            raise_404(fileId)
        perm = {
               "kind": "drive#permission",
               "etag": "Lie3Y624-6bAlCGsnUSYyb6P-dU/k6w2imYTYLSrsTHqeiu6HpWiCVQ",
               "id": get_a_uuid(),
               "name": "Test User",
               "emailAddress": self._directory._user_email,
               "domain": "testers.com",
               "role": "owner",
               "type": "user",
            }

        self._permissions[fileId].append(perm)
        return perm

    def insert(self, fileId=None, body=None, **kwargs):
        return ServiceCall(self._insert, fileId=fileId, body=body, **kwargs)


class ParentsService(object):

    def __init__(self, files=None, directory=None):
        # TODO -- add a way to pass in parent fixtures
        self._directory = directory
        self._parents = {}
        files = files or []
        for afile in files:
            self._set_default_parent(afile)

    def _set_default_parent(self, a_file):
        default_parents = {
           "kind": "drive#parentReference",
           "id": "ROOT_FOLDER_ID",
           "selfLink": "https://www.googleapis.com/drive/v2/files/%(fileId)s/parents/ROOT_FOLDER_ID" %
                       {'fileId': a_file['id']},
           "parentLink": "https://www.googleapis.com/drive/v2/files/ROOT_FOLDER_ID",
           "isRoot": True
          }
        self._parents[a_file['id']] = [default_parents]

    def _list(self, fileId=None, **kwargs):
        if fileId not in self._parents:
            raise_404(fileId)
        response = {
             "kind": "drive#parentList",
            "items": self._parents[fileId]
        }
        return response

    def list(self, fileId=None, **kwargs):
        return ServiceCall(self._list, fileId=fileId, **kwargs)

    def _insert(self, fileId=None, body=None, **kwargs):
        if fileId not in self._parents:
            raise_404(fileId)
        # don't add something twice
        for parent in self._parents[fileId]:
            if parent['id'] == body['id']:
                return parent

        parent_data = {
           "kind": "drive#parentReference",
           "id": body['id'],
           "selfLink": "https://www.googleapis.com/drive/v2/files/%(fileId)s/parents/%(parentId)s" %
                       {'fileId': fileId, 'parentId': body['id']},
           "parentLink": "https://www.googleapis.com/drive/v2/files/%s" % body['id'],
           "isRoot": False
        }
        self._parents[fileId].append(parent_data)
        return parent_data

    def insert(self, fileId=None, body=None, **kwargs):
        return ServiceCall(self._insert, fileId=fileId, body=body, **kwargs)

    def _delete(self, fileId=None, parentId=None, **kwargs):
        if fileId not in self._parents:
            raise_404(fileId)
        parents = self._parents[fileId]
        for parent in parents:
            if parent['id'] == parentId:
                parents.remove(parent)
                break
        return {}

    def delete(self, fileId=None, parentId=None, **kwargs):
        return ServiceCall(self._delete, fileId=fileId, parentId=parentId, **kwargs)


class ServiceDirectory(object):

    def __init__(self, files=None, user_email="test@drivetestbed.org"):
        self._path_map = {}
        self._user_email = user_email
        self._files = FilesService(files=files, directory=self)
        self._path_map[self._files.path] = self._files
        self._permissions = PermissionsService(files=files, directory=self)
        self._parents = ParentsService(files=files, directory=self)

    def add_mapping(self, service, path):
        """
        Callback from service to set up request path that the service responds to
        :param service:
        :param path:
        :return:
        """
        self._path_map[path] = service

    def files(self):
        return self._files

    def permissions(self):
        return self._permissions

    def parents(self):
        return self._parents

    def for_path(self, path):
        return self._path_map.get(path)


class ServiceStub(object):

    # TODO -- add something to create a fixture service with pre-set files, etc.

    @classmethod
    def get_service(cls, files=None):
        '''
        This creates a new empty service every time
        :return:
        '''
        return ServiceDirectory(files=files)
