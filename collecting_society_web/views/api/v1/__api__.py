# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.service import get_services
from cornice_swagger.swagger import CorniceSwagger
from . import apiversion

# Create a service to serve our OpenAPI spec
swagger = Service(name='OpenAPI',
                  path=apiversion+'/__api__',
                  description="OpenAPI documentation",
                  )


@swagger.get(permission=NO_PERMISSION_REQUIRED)
def openAPI_spec(request):
    services = get_services(
        names=[
            'collection_artist', 'artist',
            'collection_creation', 'creation',
            'collection_release', 'release',
        ])
    my_generator = CorniceSwagger(services)
    my_generator.summary_docstrings = True
    my_generator.base_path = ''
    my_spec = my_generator('Repertoire API', '1.0.0')
    return my_spec
