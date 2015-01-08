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

    def test_404_get(self, service):
        with pytest.raises(HttpError):
            response = service.files().get(fileId="fred").execute()

