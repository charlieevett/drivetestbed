from apiclient.errors import HttpError
from drivetestbed.services import ServiceStub
import pytest


class TestServiceDirectory(object):

    def test_file_service_create(self):
        service = ServiceStub.get_service()
        files = service.files()
        assert files


@pytest.fixture
def service():
    return ServiceStub.get_service()


ONE_FILE_ID = "ONE_TEST_FILE"


@pytest.fixture
def one_file_service():
    test_file = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain',
            'id': ONE_FILE_ID
        }
    return ServiceStub.get_service(files=[test_file])


class TestFilesService(object):

    def test_empty_files_list(self, service):
        response = service.files().list().execute()
        assert response
        assert 'items' in response
        assert len(response['items']) == 0
        assert 'etag' in response
        assert response.get('kind') == 'drive#fileList'

    def test_insert_file(self, service):
        body = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain'
        }
        response = service.files().insert(body=body).execute()
        assert response
        assert response.get('id')
        assert response.get('title') == body['title']
        assert response.get('description') == body['description']
        assert response.get('mimeType') == body['mimeType']
        # now see if you can get the file again
        response = service.files().get(fileId=response['id'])
        assert response

    def test_list_after_insert(self, service):
        body = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain'
        }
        insert_response = service.files().insert(body=body).execute()

        response = service.files().list().execute()
        assert response
        assert 'items' in response
        assert len(response['items']) == 1
        assert response['items'][0]['id'] == insert_response['id']

    def test_404_get(self, service):
        with pytest.raises(HttpError):
            response = service.files().get(fileId="fred").execute()

    def test_delete(self, one_file_service):
        response = one_file_service.files().delete(fileId=ONE_FILE_ID).execute()
        assert response is not None
        # file should be gone now
        list_response = one_file_service.files().list().execute()
        assert not list_response['items']

    def test_copy(self, one_file_service):
        copied_file = {'title': "A copied test file"}
        response = one_file_service.files().copy(fileId=ONE_FILE_ID, body=copied_file).execute()
        assert response
        assert response.get('title') == copied_file['title']
        # should have two files now
        list_response = one_file_service.files().list().execute()
        assert len(list_response['items']) == 2

    def test_404_copy(self, service):
        copied_file = {'title': "A copied test file"}
        with pytest.raises(HttpError):
            response = service.files().copy(fileId=ONE_FILE_ID, body=copied_file).execute()


class TestPermissionsService(object):

    def test_get_permissions_stub(self, service):
        assert service.permissions()

    def test_file_404_get(self, service):
        with pytest.raises(HttpError):
            response = service.permissions().get(fileId="fred", permissionId="fred").execute()

    def test_perm_404_get(self, one_file_service):
        with pytest.raises(HttpError):
            response = one_file_service.permissions().get(fileId=ONE_FILE_ID, permissionId="fred").execute()

    def test_default_permissions_list(self, one_file_service):
        response = one_file_service.permissions().list(fileId=ONE_FILE_ID).execute()
        assert response
        assert 'items' in response
        assert len(response['items']) == 1
        assert 'etag' in response
        assert response.get('kind') == 'drive#permissionList'

class TestFilesAndPermissions(object):

    def test_insert_file_owner_permission(self, service):
        body = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain'
        }
        response = service.files().insert(body=body).execute()
        # now look for the permissions
        perms = service.permissions().list(fileId=response["id"]).execute()
        assert len(perms['items']) == 1

