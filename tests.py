from apiclient.errors import HttpError
from apiclient.discovery import build
from drivetestbed import http
from apiclient import discovery
import pytest


ONE_FILE_ID = "ONE_TEST_FILE"


@pytest.fixture
def service():
    return build('drive', 'v2', http.TestbedHttp())


@pytest.fixture
def one_file_service():
    test_file = {
        'title': "test",
        'description': "test description",
        'mimeType': 'text/plain',
        'id': ONE_FILE_ID
    }
    return build('drive', 'v2', http.TestbedHttp(files=[test_file]))


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

    def test_create_with_user(self):
        service = build('drive', 'v2', http.TestbedHttp(files=[], user_email="usertest@drivetestbed.org"))
        body = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain'
        }
        insert_response = service.files().insert(body=body).execute()

        response = service.files().list().execute()
        assert len(response['items']) == 1
        new_file = response['items'][0]
        assert len(new_file['owners']) == 1
        assert new_file['owners'][0]['emailAddress'] == "usertest@drivetestbed.org"


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

    def test_get_id_for_email(self, service):
        response = service.permissions().getIdForEmail(email="fred@gmail.com").execute()
        assert response
        assert response['kind'] == "drive#permissionId"
        assert response['id']

    def test_insert_permission(self, one_file_service):
        new_permission = {
            'value': 'test_reader@drivetestbed.org',
            'type': 'user',
            'role': 'reader'
        }
        response = one_file_service.permissions().insert(fileId=ONE_FILE_ID, body=new_permission).execute()
        assert response.get('kind') == 'drive#permission'
        response = one_file_service.permissions().list(fileId=ONE_FILE_ID).execute()
        assert len(response['items']) == 2
        assert [perm for perm in response['items'] if perm['emailAddress'] == 'test_reader@drivetestbed.org' and
                perm['type'] == 'user' and perm['role'] == 'reader']

    def test_insert_group_permission(self, one_file_service):
        new_permission = {
            'value': 'group@drivetestbed.org',
            'type': 'group',
            'role': 'reader'
        }
        response = one_file_service.permissions().insert(fileId=ONE_FILE_ID, body=new_permission).execute()
        assert response.get('kind') == 'drive#permission'
        response = one_file_service.permissions().list(fileId=ONE_FILE_ID).execute()
        assert len(response['items']) == 2
        assert [perm for perm in response['items'] if perm['emailAddress'] == 'group@drivetestbed.org' and
                perm['type'] == 'group' and perm['role'] == 'reader']

    def test_insert_domain_permission(self, one_file_service):
        new_permission = {
            'value': 'drivetestbed.org',
            'type': 'domain',
            'role': 'reader'
        }
        response = one_file_service.permissions().insert(fileId=ONE_FILE_ID, body=new_permission).execute()
        assert response.get('kind') == 'drive#permission'
        response = one_file_service.permissions().list(fileId=ONE_FILE_ID).execute()
        assert len(response['items']) == 2
        assert [perm for perm in response['items'] if perm['domain'] == 'drivetestbed.org' and
                perm['type'] == 'domain' and perm['role'] == 'reader']

    def test_insert_all_permission(self, one_file_service):
        new_permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        response = one_file_service.permissions().insert(fileId=ONE_FILE_ID, body=new_permission).execute()
        assert response.get('kind') == 'drive#permission'
        response = one_file_service.permissions().list(fileId=ONE_FILE_ID).execute()
        assert len(response['items']) == 2
        assert [perm for perm in response['items'] if perm['type'] == 'anyone' and perm['role'] == 'reader']

    def test_delete_permission(self, one_file_service):
        new_permission = {
            'value': 'drivetestbed.org',
            'type': 'domain',
            'role': 'reader'
        }
        response = one_file_service.permissions().insert(fileId=ONE_FILE_ID, body=new_permission).execute()
        one_file_service.permissions().delete(fileId=ONE_FILE_ID, permissionId=response['id']).execute()
        response = one_file_service.permissions().list(fileId=ONE_FILE_ID).execute()
        assert len(response['items']) == 1


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


class TestParentsService(object):
    def test_get_parents_stub(self, service):
        assert service.parents()

    def test_insert_file_default_parents(self, service):
        body = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain'
        }
        response = service.files().insert(body=body).execute()
        # now look for the parents
        perms = service.parents().list(fileId=response["id"]).execute()
        assert len(perms['items']) == 1

    def test_insert_into_folder(self, one_file_service):
        # make a folder
        body = {
            'title': "test folder",
            'description': "test description",
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = one_file_service.files().insert(body=body).execute()
        insert_body = {
            'id': response['id']
        }
        response = one_file_service.parents().insert(fileId=ONE_FILE_ID, body=insert_body).execute()
        # now see that list has the new one
        perms = one_file_service.parents().list(fileId=ONE_FILE_ID).execute()
        assert len(perms['items']) == 2

    def test_insert_twice_into_folder(self, one_file_service):
        # make a folder
        body = {
            'title': "test folder",
            'description': "test description",
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = one_file_service.files().insert(body=body).execute()
        insert_body = {
            'id': response['id']
        }
        # call it twice and still should have only one
        response = one_file_service.parents().insert(fileId=ONE_FILE_ID, body=insert_body).execute()
        response = one_file_service.parents().insert(fileId=ONE_FILE_ID, body=insert_body).execute()
        # now see that list has the new one
        perms = one_file_service.parents().list(fileId=ONE_FILE_ID).execute()
        assert len(perms['items']) == 2

    def test_insert_and_delete_into_folder(self, one_file_service):
        # make a folder
        body = {
            'title': "test folder",
            'description': "test description",
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = one_file_service.files().insert(body=body).execute()
        insert_body = {
            'id': response['id']
        }
        response = one_file_service.parents().insert(fileId=ONE_FILE_ID, body=insert_body).execute()
        one_file_service.parents().delete(fileId=ONE_FILE_ID, parentId=response['id']).execute()
        # now see that list has the new one
        perms = one_file_service.parents().list(fileId=ONE_FILE_ID).execute()
        assert len(perms['items']) == 1


class TestClientCall(object):

    def test_drive_build(self):
        test_file = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain',
            'id': ONE_FILE_ID
        }

        drive_service = discovery.build('drive', 'v2', http.TestbedHttp(files=[test_file]))
        assert drive_service


class TestGlobalService(object):

    def test_create_global_service(self):

        test_file = {
            'title': "test global",
            'description': "test global description",
            'mimeType': 'text/plain',
            'id': "GLOBAL_FILE_ID"
        }
        try:
            http.TestbedHttp.setup_global_service(files=[test_file])
            drive_service = discovery.build('drive', 'v2', http.TestbedHttp())
            response = drive_service.files().list().execute()
            assert response
            assert 'items' in response
            assert len(response['items']) == 1
            assert response['items'][0]['id'] == "GLOBAL_FILE_ID"
        finally:
            http.TestbedHttp.teardown_global_service()

