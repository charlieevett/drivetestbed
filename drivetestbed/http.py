# mock http service that intercepts calls to allow Drive to work locally
import json
from urlparse import urlparse
from httplib2 import Response
from drivetestbed.services import ServiceDirectory


class TestbedHttp(object):

    def __init__(self, files=None):
        self._services = ServiceDirectory(files)

    def request(self, uri, method="GET", body=None, **kwargs):
        # figure out how to dispatch the URL
        # TODO -- look into setting up a Flask app or something to do routing

        parsed_uri = urlparse(uri)
        if 'discovery' in parsed_uri.path:
            resp = Response({'status': 200, 'reason': 'OK'})
            fp = file("drivetestbed/schema.json", 'r')
            try:
                content = fp.read()
            finally:
              fp.close()
            return (resp, content)
        else:
            path = parsed_uri.path.split("/drive/v2/")[1]
            service = self._services.for_path(path)
            data = service.request(path, parsed_uri.query)
            resp = Response({'status': 200, 'reason': 'OK'})
            return (resp, json.dumps(data))
