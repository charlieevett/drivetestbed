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
        files = files or []
        for afile in files:
            if 'id' not in afile:
                afile['id'] = get_a_uuid()
            self._files[afile['id']] = afile
        self._directory = directory

    @property
    def path(self):
        return "files"

    @property
    def name(self):
        return "files"

    def list(self, **kwargs):
        response = {
            "kind": "drive#fileList",
            "etag": "\"ALmZNavQ1pakoTwofyfJ4wBG6iY/vyGp6PvFo4RvsFtPoIWeCReyIC8\"",
            "selfLink": "https://www.googleapis.com/drive/v2/files?q=trashed+%3D+false",
            "items": self._files.values()
        }
        return response

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
        self._directory.permissions()._set_default_permissions(response)
        self._directory.parents()._set_default_parent(response)
        return response

    def get(self, fileId=None, **kwargs):
        file = self._files.get(fileId)
        if file:
            return file
        else:
            raise_404(fileId)

    def delete(self, fileId=None, **kwargs):
        if fileId not in self._files:
            raise_404(fileId)
        del self._files[fileId]
        return {}

    def copy(self, fileId=None, body=None, **kwargs):
        if fileId not in self._files:
            raise_404(fileId)
        file_copy = self._files[fileId].copy()
        if body:
            for key in body.keys():
                file_copy[key] = body[key]
        return self.insert(body=file_copy)

    def request(self, path, method='GET', **kwargs):
        """
        :param uri: The parsed URI of the request
        :param method:
        :return:
        """
        if path.endswith("files"):
            if method == 'GET':
                return self.list()
            elif method == 'POST':
                return self.insert(**kwargs)
        else:
            raise Exception("no method for path: %s" % path)


class PermissionsService(object):

    def __init__(self, files=None, directory=None):
        self._directory = directory
        self._permissions = {}
        files = files or []
        for afile in files:
            self._set_default_permissions(afile)

    @property
    def path(self):
        return "permissions"

    @property
    def name(self):
        return "permissions"

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

    def get(self, fileId=None, permissionId=None, **kwargs):
        if fileId not in self._permissions:
            raise_404(fileId)
        perms = self._permissions[fileId]
        for permission in perms:
            if permission['id'] == permissionId:
                return permission
        raise_404(fileId, msg="Permission not found: %s" % permissionId)

    def list(self, fileId=None, **kwargs):
        if fileId not in self._permissions:
            raise_404(fileId)
        response = {
            "kind": "drive#permissionList",
            "etag": "AFakeETag",
            "items": self._permissions[fileId]
        }
        return response

    def getIdForEmail(self, email=None, **kwargs):
        response = {
            "kind": "drive#permissionId",
            "id": str(hash(email))
        }
        return response

    def insert(self, fileId=None, body=None, **kwargs):
        if fileId not in self._permissions:
            raise_404(fileId)
        # TODO -- hash value into ID
        id = body.get('value')
        if body['type'] == 'user' or body['type'] == 'group':
            domain = body['value'].split('@')[1]
            email = body['value']
        elif body['type'] == 'domain':
            domain = body['value']
            email = ""
        else:
            domain = ""
            email = ""
        perm = {
               "kind": "drive#permission",
               "etag": "Lie3Y624-6bAlCGsnUSYyb6P-dU/k6w2imYTYLSrsTHqeiu6HpWiCVQ",
               "id": id,
               "name": "Test User",
               "emailAddress": email,
               "domain": domain,
               "role": body['role'],
               "type": body['type'],
            }

        self._permissions[fileId].append(perm)
        return perm

    def request(self, path, method='GET', **kwargs):
        """
        :param uri: The parsed URI of the request
        :param method:
        :return:
        """
        if path.endswith(self.path):
            if method == 'GET':
                return self.list()
            elif method == 'POST':
                return self.insert(**kwargs)
        else:
            raise Exception("no method for path: %s" % path)


class ParentsService(object):

    def __init__(self, files=None, directory=None):
        # TODO -- add a way to pass in parent fixtures
        self._directory = directory
        self._parents = {}
        files = files or []
        for afile in files:
            self._set_default_parent(afile)

    @property
    def path(self):
        return "parents"

    @property
    def name(self):
        return "parents"

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

    def list(self, fileId=None, **kwargs):
        if fileId not in self._parents:
            raise_404(fileId)
        response = {
             "kind": "drive#parentList",
            "items": self._parents[fileId]
        }
        return response

    def insert(self, fileId=None, body=None, **kwargs):
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

    def delete(self, fileId=None, parentId=None, **kwargs):
        if fileId not in self._parents:
            raise_404(fileId)
        parents = self._parents[fileId]
        for parent in parents:
            if parent['id'] == parentId:
                parents.remove(parent)
                break
        return {}

    def request(self, path, method='GET', **kwargs):
        """
        :param uri: The parsed URI of the request
        :param method:
        :return:
        """
        if path.endswith(self.path):
            return self.list()
        else:
            raise Exception("no method for path: %s" % path)

class ServiceDirectory(object):

    def __init__(self, files=None, user_email="test@drivetestbed.org"):
        self._path_map = {}
        self._name_map = {}
        self._user_email = user_email
        for cls in [FilesService, PermissionsService, ParentsService]:
            serv = cls(files=files, directory=self)
            self._path_map[serv.path] = serv
            self._name_map[serv.name] = serv

    def add_mapping(self, service, path):
        """
        Callback from service to set up request path that the service responds to
        :param service:
        :param path:
        :return:
        """
        self._path_map[path] = service

    def files(self):
        return self.for_path('files')

    def permissions(self):
        return self.for_path('permissions')

    def parents(self):
        return self.for_path('parents')

    def for_name(self, name):
        return self._name_map[name]

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
