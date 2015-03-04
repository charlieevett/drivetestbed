# drivetestbed

Drive TestBed is a mock Google Drive API implementation that actually "works".

You construct Drive service calls as you normally would using the Python client but instead of making calls to an actual gdocs domain they are routed to a local in-memory database of documents and permissions.

This allows you to test the side effects of a Drive app without having to be connected to a gdocs domain and with much greater performance, since their is no http overhead.

Conceptually, this is modeled on the App Engine Testbed provided with Google App Engine.

## Services supported

Currently the following services are at some stage of support:

* Files
* Permissions
* Children

## Integrating into your tests

Still trying to figure this out.
