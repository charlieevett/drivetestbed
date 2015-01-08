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

@pytest.fixture
def one_file_service():
    test_file = {
            'title': "test",
            'description': "test description",
            'mimeType': 'text/plain'
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
        files = one_file_service.files().list().execute()
        file_id = files['items'][0]['id']
        response = one_file_service.files().delete(fileId=file_id).execute()
        assert response is not None
        # file should be gone now
        list_response = one_file_service.files().list().execute()
        assert not list_response['items']




