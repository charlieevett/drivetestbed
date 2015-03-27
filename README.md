# drivetestbed

Drive TestBed is a mock Google Drive API implementation that actually "works".

You construct Drive service calls as you normally would using the Python client but instead of making calls to an actual gdocs domain they are routed to a local in-memory database of documents and permissions.

This allows you to test the side effects of a Drive app without having to be connected to a gdocs domain and with much greater performance, since there is no http overhead.

Conceptually, this is modeled on the App Engine Testbed provided with Google App Engine.

## Services supported

Currently the following services are at some stage of support:

* Files
* Permissions
* Parents

## Integrating into your tests

The drive testbed works by replacing the Http connection to the Drive service. The easiest way to set this
up is to substitute the testbed http when building the service using the discovery API. For example:

    from apiclient.discovery import build
    
    service = build('drive', 'v2', http.TestbedHttp())

Then you can use the service in the normal way:

    response = service.files().list().execute()
    
## Dependencies

Need to put together a build with requirements.txt
Until then, you need:

    pip install routes
    pip install google-api-python-client
