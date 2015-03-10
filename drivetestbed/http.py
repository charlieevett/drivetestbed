# mock http service that intercepts calls to allow Drive to work locally
import json
from urlparse import urlparse, parse_qs
from httplib2 import Response
from drivetestbed.services import ServiceDirectory
from routes import Mapper


class TestbedHttp(object):

    def __init__(self, files=None, **kwargs):
        self._services = ServiceDirectory(files)

    def request(self, uri, method="GET", body=None, **kwargs):
        parsed_uri = urlparse(uri)
        if 'discovery' in parsed_uri.path:
            # TODO -- use Routes for discovery service as well
            resp = Response({'status': 200, 'reason': 'OK'})
            fp = file("drivetestbed/schema.json", 'r')
            try:
                content = fp.read()
            finally:
              fp.close()
            schema = json.loads(content)
            path_dict = {}
            map = Mapper()
            with map.submapper(path_prefix="/drive/v2/") as m:
                for r_name, r_data in schema['resources'].iteritems():
                    for meth_name, meth_data in r_data['methods'].iteritems():
                        m.connect(meth_data['path'], conditions={'method': [meth_data['httpMethod']]},
                                    controller=r_name, action=meth_name)
            self._map = map
            return (resp, content)
        else:
            environ = {'REQUEST_METHOD': method}
            matched = self._map.match(parsed_uri.path, environ=environ)
            if matched:
                query_params = parse_qs(parsed_uri.query)
                # unwrap single value params from list
                for key in query_params.keys():
                    if len(query_params[key]) == 1:
                        query_params[key] = query_params[key][0]

                if body:
                    query_params['body'] = json.loads(body)
                service = self._services.for_name(matched['controller'])
                action_func = getattr(service, matched['action'])
                if action_func:
                    del matched['controller']
                    del matched['action']
                    query_params.update(matched)
                    data = action_func(**query_params)
                else:
                    return (Response({'status': 404, 'reason': 'No such action: %s' % matched['action']}), "")
                resp = Response({'status': 200, 'reason': 'OK'})
                return (resp, json.dumps(data))
            else:
                return (Response({'status': 404, 'reason': 'Bad request'}), "")
